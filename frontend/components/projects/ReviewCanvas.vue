<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Checkbox } from '~/components/ui/checkbox'
import { Label } from '~/components/ui/label'
import { useCanvasInteraction } from '~/composables/useCanvasInteraction'
import { useLayerManager } from '~/composables/useLayerManager'
import CanvasOverlays from '~/components/projects/CanvasOverlays.vue'
import CommentIcon from '~/components/projects/CommentIcon.vue'
import ProjectModelViewer from '~/components/projects/ProjectModelViewer.vue'
import type { ViewerView } from '~/types/viewer'
import type { CommentThread } from '~/types/api/commentThreads'

export type PinViewerAnnotation = {
  id: string
  tool: 'pin'
  pinX: number
  pinY: number
  data: {
    initial: string
    comment: string
    authorName: string
    color?: string
  }
}
export type ViewerAnnotation = PinViewerAnnotation

const props = withDefaults(
  defineProps<{
    views?: ViewerView[]
    initialViewId?: string
    activeTool?: 'pan' | 'pin'
    annotations?: Record<string, ViewerAnnotation[]>
    highlightedThreadId?: string | null
    pendingPin?: { x: number, y: number } | null
    activeThread?: CommentThread | null
    currentUserInitial?: string
    canResolveThreads?: boolean
    authorColorMap?: Map<string, string>
    currentUserColor?: string
  }>(),
  {
    views: () => [],
    activeTool: 'pan',
    annotations: () => ({}),
    highlightedThreadId: null,
    pendingPin: null,
    activeThread: null,
    currentUserInitial: 'G',
    canResolveThreads: false,
    currentUserColor: '#FFD02B',
  },
)

const emit = defineEmits<{
  viewChange: [viewId: string]
  pinCreated: [
    {
      viewId: string
      pinX: number
      pinY: number
      tool: 'pin'
      data: { initial: string, comment: string, authorName: string }
    },
  ]
  pinClick: [annotationId: string]
  pinHover: [annotationId: string]
  pinLeave: [annotationId: string]

  submitComment: [content: string]
  cancelComment: []
  submitReply: [content: string]
  resolveThread: [thread: CommentThread]
  closeThread: []
}>()

const contentRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)
const modelViewerRef = ref<InstanceType<typeof ProjectModelViewer> | null>(null)
const assetBounds = ref<DOMRect | null>(null)
const modelBounds = ref<DOMRect | null>(null)

const activeViewId = ref<string | null>(null)
const activeView = computed(() => props.views.find(v => v.id === activeViewId.value) ?? props.views[0])
const composedAsset = computed(() => activeView.value?.asset ?? null)
const activeAsset = computed(() => composedAsset.value ?? activeView.value?.asset)

const {
  availableLayers,
  isMultiLayer,
  visibleLayerIds,
  firstVisibleLayerId,
  bottomVisibleLayerId,
  toggleLayer,
} = useLayerManager(activeView)

const is3DView = computed(() => activeView.value?.kind === '3d')
const isLayoutView = computed(() => !is3DView.value && (activeView.value?.id?.startsWith('pcb') || isMultiLayer.value))
const layoutBackgroundStyle = computed(() => (isLayoutView.value ? { backgroundColor: '#001124' } : undefined))

const disablePan = computed(() => props.activeTool !== 'pan' || is3DView.value)

const {
  zoom,
  translate,
  isPanning,
  adjustZoom,
  setZoom,
  resetTranslate,
  handleWheel,
  handlePointerDown,
  stopPanning,
  handlePointerMove,
} = useCanvasInteraction(contentRef, { disableInteraction: disablePan })

function handleCombinedPointerMove(e: PointerEvent) {
  handleCursorMove(e)
  handlePointerMove(e)
}

function setActiveView(viewId: string) {
  if (activeViewId.value === viewId) return
  if (!props.views.some(view => view.id === viewId)) return
  activeViewId.value = viewId
}

watch(
  () => props.views,
  (views) => {
    if (!views.length) {
      activeViewId.value = null
      return
    }
    if (activeViewId.value && views.some(v => v.id === activeViewId.value)) return
    const fallback = props.initialViewId && views.some(v => v.id === props.initialViewId) ? props.initialViewId : views[0]!.id
    activeViewId.value = fallback
  },
  { immediate: true },
)

const naturalWidth = ref(0)
const naturalHeight = ref(0)
const hasInitializedView = ref(false)

watch(activeViewId, (val) => {
  if (!val) return
  emit('viewChange', val)
  naturalWidth.value = 0
  naturalHeight.value = 0
  hasInitializedView.value = false
  resetView()
})

function resetView() {
  resetTranslate()
  // First set zoom to 1 to get proper baseline measurements
  setZoom(1)
  nextTick(() => {
    const initialZoom = computeInitialZoom()
    setZoom(initialZoom)
    nextTick(() => updateAssetBounds())
  })
}

function computeInitialZoom() {
  if (!contentRef.value) return 1

  const viewport = contentRef.value.getBoundingClientRect()
  if (viewport.width === 0 || viewport.height === 0) return 1

  // If image is rendered, use its actual displayed size (after CSS constraints)
  // This accounts for max-h-[70vh] max-w-[80vw] CSS constraints
  if (imageRef.value) {
    const imgRect = imageRef.value.getBoundingClientRect()
    // Since zoom is set to 1 before this runs, imgRect gives us the base size
    const currentZoom = zoom.value || 1
    const baseW = imgRect.width / currentZoom
    const baseH = imgRect.height / currentZoom

    if (baseW > 0 && baseH > 0) {
      // Account for toolbar at top (~60px) and some padding
      const availableHeight = viewport.height - 80
      const availableWidth = viewport.width - 40

      // Use 1.15x multiplier to fill more of the screen (ok if slightly cut off)
      const scaleX = (availableWidth * 1.15) / baseW
      const scaleY = (availableHeight * 1.15) / baseH
      const scale = Math.min(scaleX, scaleY)
      return Math.min(20, Math.max(0.5, Number(scale.toFixed(2))))
    }
  }

  // Fallback: use natural dimensions with CSS constraint simulation
  const natW = naturalWidth.value || 800
  const natH = naturalHeight.value || 600

  if (natW === 0 || natH === 0) return 1

  // Simulate CSS constraints: max-w-[80vw] max-h-[70vh]
  const maxCssW = viewport.width * 0.8
  const maxCssH = viewport.height * 0.7
  const imageAspect = natW / natH

  let constrainedW: number, constrainedH: number
  if (natW <= maxCssW && natH <= maxCssH) {
    constrainedW = natW
    constrainedH = natH
  }
  else {
    const wForMaxW = maxCssW
    const hForMaxW = maxCssW / imageAspect
    const hForMaxH = maxCssH
    const wForMaxH = maxCssH * imageAspect

    if (hForMaxW <= maxCssH) {
      constrainedW = wForMaxW
      constrainedH = hForMaxW
    }
    else {
      constrainedW = wForMaxH
      constrainedH = hForMaxH
    }
  }

  const availableHeight = viewport.height - 80
  const availableWidth = viewport.width - 40
  // Use 1.15x multiplier to fill more of the screen (ok if slightly cut off)
  const scaleX = (availableWidth * 1.15) / constrainedW
  const scaleY = (availableHeight * 1.15) / constrainedH
  const scale = Math.min(scaleX, scaleY)
  return Math.min(20, Math.max(0.5, Number(scale.toFixed(2))))
}

function handlePointerUp(event: PointerEvent) {
  if (props.activeTool === 'pan') {
    stopPanning(event)
  }
}

const activeViewPins = computed(() => {
  const viewId = activeView.value?.id
  if (!viewId) return []
  return props.annotations?.[viewId] ?? []
})

function canvasPointerDown(e: PointerEvent) {
  if (props.activeTool !== 'pin') return

  const target = e.target as HTMLElement
  if (target.closest('.pointer-events-auto')) return

  e.preventDefault()

  if (props.pendingPin) {
    emit('cancelComment')
    return
  }

  updateAssetBounds()
  if (!assetBounds.value) return

  const rel = clientToRelative(e.clientX, e.clientY)

  emit('pinCreated', {
    viewId: activeView.value.id,
    tool: 'pin',
    pinX: rel.x,
    pinY: rel.y,
    data: { initial: props.currentUserInitial, comment: '', authorName: 'Me' },
  })
}

function clientToRelative(clientX: number, clientY: number) {
  const rect = assetBounds.value!
  const x = (clientX - rect.left) / rect.width
  const y = (clientY - rect.top) / rect.height
  return { x: Number(x.toFixed(5)), y: Number(y.toFixed(5)) }
}

watch([zoom, () => translate.value.x, () => translate.value.y], () => {
  nextTick(() => updateAssetBounds())
})

function updateAssetBounds() {
  if (is3DView.value) {
    if (modelBounds.value) {
      assetBounds.value = new DOMRect(
        modelBounds.value.x,
        modelBounds.value.y,
        modelBounds.value.width,
        modelBounds.value.height,
      )
    }
    else {
      assetBounds.value = null
    }
    return
  }
  if (!imageRef.value) {
    assetBounds.value = null
    return
  }
  const rect = imageRef.value.getBoundingClientRect()
  assetBounds.value = new DOMRect(rect.x, rect.y, rect.width, rect.height)
}

function handleImageLoad() {
  if (imageRef.value) {
    naturalWidth.value = imageRef.value.naturalWidth || imageRef.value.width
    naturalHeight.value = imageRef.value.naturalHeight || imageRef.value.height
  }
  // Reset view to properly center and zoom to fit content
  nextTick(() => {
    resetView()
    hasInitializedView.value = true
  })
}

function handleModelBounds(rect: DOMRect) {
  modelBounds.value = rect
  if (is3DView.value) {
    assetBounds.value = new DOMRect(rect.x, rect.y, rect.width, rect.height)
  }
}

function flipModelOrientation() {
  modelViewerRef.value?.toggleFlip()
}

const cursorX = ref(0)
const cursorY = ref(0)
const cursorVisible = ref(false)

function handleCursorMove(e: PointerEvent) {
  if (props.activeTool !== 'pin') return
  cursorX.value = e.clientX
  cursorY.value = e.clientY
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  window.addEventListener('resize', updateAssetBounds)

  if (contentRef.value) {
    resizeObserver = new ResizeObserver(() => {
      updateAssetBounds()
      if (!hasInitializedView.value && naturalWidth.value > 0) {
        resetView()
        hasInitializedView.value = true
      }
    })
    resizeObserver.observe(contentRef.value)
  }
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', updateAssetBounds)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

defineExpose({ adjustZoom, resetView, setActiveView, flipModel: flipModelOrientation })
</script>

<template>
  <div class="relative h-full w-full">
    <div
      v-if="is3DView"
      class="relative h-full w-full"
    >
      <ProjectModelViewer
        ref="modelViewerRef"
        :model-url="activeAsset?.url || undefined"
        :interaction-enabled="false"
        @bounds-change="handleModelBounds"
      />
      <div
        v-if="!activeAsset?.url"
        class="absolute inset-0 flex h-full w-full items-center justify-center border border-dashed border-muted-foreground/40 bg-muted/20 p-6 text-sm text-muted-foreground"
      >
        {{ activeView?.fallbackMessage ?? 'No 3D model available.' }}
      </div>

      <div
        class="absolute inset-0"
        :class="props.activeTool === 'pin' ? 'cursor-none' : ''"
        @pointermove="handleCursorMove"
        @pointerleave="cursorVisible = false"
        @pointerenter="cursorVisible = true"
        @pointerdown.capture="canvasPointerDown"
      >
        <div
          v-if="props.activeTool === 'pin' && cursorVisible"
          class="pointer-events-none fixed z-[9999] drop-shadow-md"
          :style="{ left: `${cursorX}px`, top: `${cursorY}px`, transform: 'translate(-0%, -100%)' }"
        >
          <CommentIcon
            :initial="currentUserInitial"
            size="lg"
            :color="currentUserColor"
          />
        </div>

        <CanvasOverlays
          v-if="assetBounds"
          :pins="activeViewPins"
          :active-thread-id="activeThread?.id"
          :zoom="zoom"
          :pending-pin="pendingPin"
          :active-thread="activeThread && activeThread.view_id === activeView.id ? activeThread : null"
          :current-user-initial="currentUserInitial"
          :author-color-map="authorColorMap"
          :current-user-color="currentUserColor"
          @pin-hover="(id: string) => emit('pinHover', id)"
          @pin-leave="(id: string) => emit('pinLeave', id)"
          @pin-click="(id: string) => emit('pinClick', id)"
          @submit-comment="(content: string) => emit('submitComment', content)"
          @cancel-comment="emit('cancelComment')"
          @reply="(content: string) => emit('submitReply', content)"
          @resolve-thread="(thread: CommentThread) => emit('resolveThread', thread)"
          @close-thread="emit('closeThread')"
        />
      </div>
    </div>

    <div
      v-else
      ref="contentRef"
      class="relative h-full w-full touch-none select-none"
      :style="{ cursor: props.activeTool === 'pan' ? (isPanning ? 'grabbing' : 'grab') : 'default', backgroundColor: layoutBackgroundStyle?.backgroundColor ?? 'transparent' }"
      :class="props.activeTool === 'pin' ? 'cursor-none' : ''"
      @wheel.prevent="handleWheel"
      @pointerdown="handlePointerDown"
      @pointercancel="stopPanning"
      @pointerleave="stopPanning; cursorVisible = false"
      @dblclick.prevent="resetView()"
      @pointerdown.capture="canvasPointerDown"
      @pointerup="handlePointerUp"
      @pointermove="handleCombinedPointerMove"
      @pointerenter="cursorVisible = true"
    >
      <div
        v-if="props.activeTool === 'pin' && cursorVisible"
        class="pointer-events-none fixed z-[9999] drop-shadow-md"
        :style="{ left: `${cursorX}px`, top: `${cursorY}px`, transform: 'translate(-0%, -100%)' }"
      >
        <CommentIcon
          :initial="currentUserInitial"
          size="lg"
          :color="currentUserColor"
        />
      </div>

      <div
        class="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2"
        style="user-select: none;"
      >
        <div
          class="transition-transform duration-75 ease-out"
          :style="{ transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})` }"
        >
          <div class="relative flex items-center justify-center">
            <div
              v-if="isMultiLayer"
              class="relative max-h-[70vh] max-w-[80vw]"
            >
              <template
                v-for="(layer, index) in availableLayers"
                :key="layer.id"
              >
                <img
                  v-if="visibleLayerIds.has(layer.id)"
                  :ref="(el) => { if (layer.id === firstVisibleLayerId || (visibleLayerIds.has(layer.id) && !imageRef)) imageRef = el as HTMLImageElement }"
                  :src="layer.url || ''"
                  :alt="layer.title"
                  draggable="false"
                  loading="lazy"
                  decoding="async"
                  class="max-h-[70vh] max-w-[80vw] transition-opacity duration-200"
                  :class="layer.id === firstVisibleLayerId ? 'relative' : 'absolute left-0 top-0'"
                  :style="{
                    zIndex: availableLayers.length - index,
                    opacity: (visibleLayerIds.size > 1 && layer.id !== bottomVisibleLayerId) ? 0.8 : 1,
                    mixBlendMode: visibleLayerIds.size > 1 ? 'screen' : 'normal',
                  }"
                  @dragstart.prevent
                  @load="handleImageLoad"
                >
              </template>

              <CanvasOverlays
                v-if="assetBounds"
                :pins="activeViewPins"
                :active-thread-id="activeThread?.id"
                :zoom="zoom"
                :pending-pin="pendingPin"
                :active-thread="activeThread && activeThread.view_id === activeView.id ? activeThread : null"
                :current-user-initial="currentUserInitial"
                :author-color-map="authorColorMap"
                :current-user-color="currentUserColor"
                @pin-hover="(id: string) => emit('pinHover', id)"
                @pin-leave="(id: string) => emit('pinLeave', id)"
                @pin-click="(id: string) => emit('pinClick', id)"
                @submit-comment="(content: string) => emit('submitComment', content)"
                @cancel-comment="emit('cancelComment')"
                @reply="(content: string) => emit('submitReply', content)"
                @resolve-thread="(thread: CommentThread) => emit('resolveThread', thread)"
                @close-thread="emit('closeThread')"
              />
            </div>

            <div
              v-else-if="activeAsset?.url"
              class="relative"
            >
              <img
                ref="imageRef"
                :src="activeAsset.url"
                :alt="activeAsset.title ?? 'Preview asset'"
                draggable="false"
                loading="lazy"
                decoding="async"
                class="max-h-[70vh] max-w-[80vw]"
                @dragstart.prevent
                @load="handleImageLoad"
              >

              <CanvasOverlays
                v-if="assetBounds"
                :pins="activeViewPins"
                :active-thread-id="activeThread?.id"
                :zoom="zoom"
                :pending-pin="pendingPin"
                :active-thread="activeThread && activeThread.view_id === activeView.id ? activeThread : null"
                :current-user-initial="currentUserInitial"
                :author-color-map="authorColorMap"
                :current-user-color="currentUserColor"
                @pin-hover="(id: string) => emit('pinHover', id)"
                @pin-leave="(id: string) => emit('pinLeave', id)"
                @pin-click="(id: string) => emit('pinClick', id)"
                @submit-comment="(content: string) => emit('submitComment', content)"
                @cancel-comment="emit('cancelComment')"
                @reply="(content: string) => emit('submitReply', content)"
                @resolve-thread="(thread: CommentThread) => emit('resolveThread', thread)"
                @close-thread="emit('closeThread')"
              />
            </div>

            <div
              v-else
              class="flex h-[420px] w-[720px] max-w-[85vw] items-center justify-center border border-dashed border-muted-foreground/40 bg-muted/20 p-6 text-sm text-muted-foreground"
            >
              {{ activeView?.fallbackMessage ?? 'No asset available.' }}
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="isMultiLayer"
        class="absolute right-4 top-4 z-20 rounded-md border bg-card/90 p-3 shadow-sm backdrop-blur"
        @pointerdown.stop
        @dblclick.stop
      >
        <h4 class="mb-2 text-xs font-semibold text-muted-foreground">
          Layers
        </h4>
        <div class="flex flex-col gap-2">
          <div
            v-for="layer in availableLayers"
            :key="layer.id"
            class="flex items-center gap-2"
          >
            <Checkbox
              :id="`layer-${layer.id}`"
              :model-value="visibleLayerIds.has(layer.id)"
              @update:model-value="(val: boolean) => toggleLayer(layer.id, val)"
            />
            <Label
              :for="`layer-${layer.id}`"
              class="text-xs cursor-pointer select-none"
            >{{ layer.title
            }}</Label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.touch-none {
  touch-action: none;
}

.cursor-comment {
  cursor: url("data:image/svg+xml;utf8,<svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V7C3 6.46957 3.21071 5.96086 3.58579 5.58579C3.96086 5.21071 4.46957 5 5 5H19C19.5304 5 20.0391 5.21071 20.4142 5.58579C20.7893 5.96086 21 6.46957 21 7V15Z' fill='%23FFD02B' stroke='white' stroke-width='2'/></svg>") 0 24, auto;
}
</style>
