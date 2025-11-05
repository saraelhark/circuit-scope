<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import type { PreviewAsset } from "~/types/api/projects"

export type ViewerView = {
  id: string
  label: string
  asset?: PreviewAsset | null
  fallbackMessage?: string
  pages?: PreviewAsset[]
}

export type CircleViewerAnnotation = {
  id: string
  tool: "circle"
  pinX: number
  pinY: number
  data: {
    radius: number
  }
}
export type ViewerAnnotation = CircleViewerAnnotation

const props = withDefaults(
  defineProps<{
    views: ViewerView[]
    initialViewId?: string
    activeTool: "pan" | "circle"
    annotations?: Record<string, ViewerAnnotation[]>
  }>(),
  {
    views: () => [],
    activeTool: "pan",
    annotations: () => ({}),
  },
)

const emit = defineEmits<{
  viewChange: [viewId: string]
  shapeCreated: [
    (
      | ({
        viewId: string
        pinX: number
        pinY: number
      } & CircleViewerAnnotation)
    )
  ]
}>()

const zoom = ref(1)
const minZoom = 0.25
const maxZoom = 6
const zoomStep = 0.2
const translate = ref({ x: 0, y: 0 })

const panOrigin = ref({ x: 0, y: 0 })
const pointerStart = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const activePointerId = ref<number | null>(null)

const contentRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

const assetBounds = ref<DOMRect | null>(null)

const activeViewId = ref<string | null>(null)
const activeView = computed(() => props.views.find((v) => v.id === activeViewId.value) ?? props.views[0])
const composedAsset = computed(() => activeView.value?.asset ?? null)
const activeAsset = computed(() => composedAsset.value ?? activeView.value?.asset)
const isLayoutView = computed(() => activeView.value?.id?.startsWith("pcb"))
const layoutBackgroundStyle = computed(() => (isLayoutView.value ? { backgroundColor: "#001124" } : undefined))
const annotationColor = "#7CFF00"

function setActiveView(viewId: string) {
  if (activeViewId.value === viewId) return
  if (!props.views.some((view) => view.id === viewId)) return
  activeViewId.value = viewId
}

watch(
  () => props.views,
  (views) => {
    if (!views.length) {
      activeViewId.value = null
      return
    }
    if (activeViewId.value && views.some((v) => v.id === activeViewId.value)) return
    const fallback = props.initialViewId && views.some((v) => v.id === props.initialViewId) ? props.initialViewId : views[0]!.id
    activeViewId.value = fallback
  },
  { immediate: true },
)

watch(activeViewId, (val) => {
  if (!val) return
  emit("viewChange", val)
  resetView()
})

function adjustZoom(direction: 1 | -1) {
  const next = Number((zoom.value + direction * zoomStep).toFixed(2))
  zoom.value = Math.min(maxZoom, Math.max(minZoom, next))
  updateAssetBounds()
}
function resetView() {
  translate.value = { x: 0, y: 0 }
  zoom.value = computeInitialZoom()
  nextTick(() => updateAssetBounds())
}
function computeInitialZoom() {
  if (!contentRef.value || !imageRef.value) return 1
  const viewport = contentRef.value.getBoundingClientRect()
  const natW = imageRef.value.naturalWidth || imageRef.value.width
  const natH = imageRef.value.naturalHeight || imageRef.value.height
  if (!natW || !natH) return 1
  const scale = Math.min((viewport.width * 0.9) / natW, (viewport.height * 0.9) / natH)
  const clamped = Math.min(maxZoom, Math.max(minZoom, scale))
  return Number(clamped.toFixed(2))
}


function handlePointerDown(event: PointerEvent) {
  if (props.activeTool !== "pan") return
  if (event.pointerType === "touch") event.preventDefault()
  if (!contentRef.value || isPanning.value) return
  isPanning.value = true
  activePointerId.value = event.pointerId
  pointerStart.value = { x: event.clientX, y: event.clientY }
  panOrigin.value = { ...translate.value }
  contentRef.value.setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (props.activeTool !== "pan") return
  if (!isPanning.value || activePointerId.value !== event.pointerId) return
  event.preventDefault()
  const dx = event.clientX - pointerStart.value.x
  const dy = event.clientY - pointerStart.value.y
  translate.value = { x: panOrigin.value.x + dx, y: panOrigin.value.y + dy }
}

function stopPanning(event: PointerEvent) {
  if (!isPanning.value || activePointerId.value !== event.pointerId) return
  isPanning.value = false
  activePointerId.value = null
  contentRef.value?.releasePointerCapture(event.pointerId)
}

function handlePointerUp(event: PointerEvent) {
  if (props.activeTool === "pan") {
    stopPanning(event)
  } else {
    canvasPointerUp(event)
  }
}

function handleWheel(e: WheelEvent) {
  if (props.activeTool !== "pan") return
  e.preventDefault()
  const delta = Math.sign(e.deltaY)
  adjustZoom(delta > 0 ? -1 : 1)
}

type DraftShape = { tool: "circle"; startX: number; startY: number; currentX: number; currentY: number }
type FinalShape = { id: string; startX: number; startY: number; endX: number; endY: number }

const draftShape = ref<null | DraftShape>(null)
const shapes = ref<Record<string, FinalShape>>({})

const persistedShapes = computed<Record<string, FinalShape[]>>(() => {
  const result: Record<string, FinalShape[]> = {}
  for (const [viewId, annotations] of Object.entries(props.annotations ?? {})) {
    result[viewId] = annotations
      .map((annotation) => {
        const radius = Number((annotation.data as any).radius ?? 0)
        if (!Number.isFinite(radius) || radius <= 0) return null
        const startX = annotation.pinX - radius
        const startY = annotation.pinY - radius
        const endX = annotation.pinX + radius
        const endY = annotation.pinY + radius
        return {
          id: annotation.id,
          startX,
          startY,
          endX,
          endY,
        }
      })
      .filter((shape): shape is FinalShape => Boolean(shape))
  }
  return result
})

const activeViewShapes = computed(() => {
  const viewId = activeView.value?.id
  if (!viewId) return [] as FinalShape[]
  const base = [...(persistedShapes.value[viewId] ?? [])]
  const draft = shapes.value[viewId]
  if (draft) base.push(draft)
  return base
})

watch(
  () => props.annotations,
  (annotations) => {
    if (!annotations) return
    const next = { ...shapes.value }
    for (const viewId of Object.keys(annotations)) {
      if (next[viewId]) delete next[viewId]
    }
    shapes.value = next
  },
  { deep: true },
)

function canvasPointerDown(e: PointerEvent) {
  if (props.activeTool !== "circle") return
  if (!imageRef.value) return
  e.preventDefault()

  updateAssetBounds()
  if (!assetBounds.value) return

  const rel = clientToRelative(e.clientX, e.clientY)
  draftShape.value = {
    tool: "circle",
    startX: rel.x,
    startY: rel.y,
    currentX: rel.x,
    currentY: rel.y,
  }
  contentRef.value?.setPointerCapture(e.pointerId)
}
function canvasPointerMove(e: PointerEvent) {
  if (!draftShape.value) return
  const rel = clientToRelative(e.clientX, e.clientY)
  draftShape.value.currentX = rel.x
  draftShape.value.currentY = rel.y
}
function canvasPointerUp(e: PointerEvent) {
  if (!draftShape.value) return
  const { startX, startY, currentX, currentY } = draftShape.value
  const centreX = (startX + currentX) / 2
  const centreY = (startY + currentY) / 2
  const radius = Math.max(Math.abs(currentX - startX), Math.abs(currentY - startY)) / 2
  emit("shapeCreated", {
    viewId: activeView.value.id,
    id: "temp",
    tool: "circle",
    pinX: centreX,
    pinY: centreY,
    data: { radius: Number(radius.toFixed(4)) },
  })

  const shape: FinalShape = {
    id: (globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2)),
    startX,
    startY,
    endX: currentX,
    endY: currentY,
  }
  shapes.value = { ...shapes.value, [activeView.value.id]: shape }
  draftShape.value = null
  contentRef.value?.releasePointerCapture(e.pointerId)
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
  if (!imageRef.value) {
    assetBounds.value = null
    return
  }
  const rect = imageRef.value.getBoundingClientRect()
  assetBounds.value = new DOMRect(rect.x, rect.y, rect.width, rect.height)
}

function handleImageLoad() {
  zoom.value = computeInitialZoom()
  nextTick(() => updateAssetBounds())
}

onMounted(() => {
  window.addEventListener("resize", updateAssetBounds)
})
onBeforeUnmount(() => {
  window.removeEventListener("resize", updateAssetBounds)
})

defineExpose({ adjustZoom, resetView, setActiveView })
</script>

<template>
  <div class="relative h-full w-full">
    <div ref="contentRef" class="relative h-full w-full touch-none select-none"
      :style="{ cursor: props.activeTool === 'pan' ? (isPanning ? 'grabbing' : 'grab') : 'crosshair', backgroundColor: layoutBackgroundStyle?.backgroundColor ?? 'transparent' }"
      @wheel.prevent="handleWheel" @pointerdown="handlePointerDown" @pointercancel="stopPanning"
      @pointerleave="stopPanning" @dblclick.prevent="resetView()" @pointerdown.capture="canvasPointerDown"
      @pointermove.capture="canvasPointerMove" @pointermove="handlePointerMove" @pointerup="handlePointerUp">
      <div class="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2" style="user-select: none;">
        <div class="transition-transform duration-75 ease-out"
          :style="{ transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})` }">
          <div class="relative flex items-center justify-center">
            <div v-if="activeAsset?.url" class="relative">
              <img ref="imageRef" :src="activeAsset.url" :alt="activeAsset.title ?? 'Preview asset'" draggable="false"
                @dragstart.prevent loading="lazy" decoding="async" @load="handleImageLoad"
                class="max-h-[70vh] max-w-[80vw]" />
              <svg v-if="assetBounds && (activeViewShapes.length || draftShape)"
                class="pointer-events-none absolute inset-0" :viewBox="`0 0 1 1`" preserveAspectRatio="none"
                :style="{ overflow: 'visible' }">
                <template v-for="shape in activeViewShapes" :key="shape.id">
                  <circle :cx="(shape.startX + shape.endX) / 2" :cy="(shape.startY + shape.endY) / 2"
                    :r="Math.max(Math.abs(shape.endX - shape.startX), Math.abs(shape.endY - shape.startY)) / 2"
                    :stroke="annotationColor" stroke-width="0.002" fill="none" />
                </template>
                <template v-if="draftShape">
                  <circle :cx="(draftShape.startX + draftShape.currentX) / 2"
                    :cy="(draftShape.startY + draftShape.currentY) / 2"
                    :r="Math.max(Math.abs(draftShape.currentX - draftShape.startX), Math.abs(draftShape.currentY - draftShape.startY)) / 2"
                    :stroke="annotationColor" stroke-width="0.002" fill="none" stroke-dasharray="0.006" />
                </template>
              </svg>
            </div>
            <div v-else
              class="flex h-[420px] w-[720px] max-w-[85vw] items-center justify-center rounded-lg border border-dashed border-muted-foreground/40 bg-muted/20 p-6 text-sm text-muted-foreground">
              {{ activeView?.fallbackMessage ?? 'No asset available.' }}
            </div>
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
</style>
