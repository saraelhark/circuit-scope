<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { Button } from "~/components/ui/button"
import { Checkbox } from "~/components/ui/checkbox"
import { Label } from "~/components/ui/label"

import ProjectModelViewer from "~/components/projects/ProjectModelViewer.vue"
import type { PreviewAsset } from "~/types/api/projects"
import type { ViewerView } from "~/types/viewer"

const props = withDefaults(
  defineProps<{
    views: ViewerView[]
    initialViewId?: string
    interactionMode?: "pan" | "pin"
    showControls?: boolean
  }>(),
  {
    views: () => [],
    initialViewId: undefined,
    interactionMode: "pan",
  },
)

const emit = defineEmits<{
  viewChange: [viewId: string]
  canvasClick: [
    {
      viewId: string
      relativeX: number
      relativeY: number
      clientX: number
      clientY: number
    },
  ]
}>()

const activeViewId = ref<string | null>(null)

const zoom = ref(1)
const minZoom = 0.25
const maxZoom = 6
const zoomStep = 0.2
const translate = ref({ x: 0, y: 0 })

const defaultViewportFill = 0.9

const panOrigin = ref({ x: 0, y: 0 })
const pointerStart = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const activePointerId = ref<number | null>(null)

const contentRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

const isAssetLoaded = ref(false)
const assetError = ref<string | null>(null)
const assetBounds = ref<DOMRect | null>(null)
const modelBounds = ref<DOMRect | null>(null)
const modelViewerRef = ref<InstanceType<typeof ProjectModelViewer> | null>(null)

const activeView = computed(() => props.views.find((view) => view.id === activeViewId.value) ?? props.views[0])
const activeAsset = computed<PreviewAsset | null | undefined>(() => activeView.value?.asset)

// Multi-layer support
const availableLayers = computed(() => activeView.value?.layers ?? [])
const isMultiLayer = computed(() => availableLayers.value.length > 0)
const visibleLayerIds = ref<Set<string>>(new Set())

const displayAsset = computed<PreviewAsset | null>(() => activeAsset.value ?? null)
const displayAssetKey = computed(() => displayAsset.value?.url ?? displayAsset.value?.path ?? "")
const displayAssetSrc = computed(() => displayAsset.value?.url ?? "")
const displayAssetAlt = computed(
  () => displayAsset.value?.title ?? displayAsset.value?.filename ?? "Preview asset",
)

const is3DView = computed(() => activeView.value?.kind === "3d")
const has2DAsset = computed(() => {
  if (isMultiLayer.value) return visibleLayerIds.value.size > 0
  const asset = displayAsset.value
  return Boolean(!is3DView.value && asset?.url && !assetError.value)
})
const isLayoutView = computed(() => !is3DView.value && (activeView.value?.id?.startsWith("pcb") || isMultiLayer.value))
const layoutBackgroundStyle = computed(() => {
  if (isLayoutView.value) return { backgroundColor: "#001124" }
  if (!is3DView.value) return { backgroundColor: "#F2F2F2" } // cs-whiteish for schematics
  return undefined
})
const showControlsBar = computed(() => props.showControls !== false)
const showZoomControls = computed(() => showControlsBar.value && !is3DView.value)
const canFlipModel = computed(() => is3DView.value && Boolean(activeAsset.value?.url))

const firstVisibleLayerId = computed(() => {
  if (!isMultiLayer.value) return null
  for (const layer of availableLayers.value) {
    if (visibleLayerIds.value.has(layer.id)) return layer.id
  }
  return null
})

const bottomVisibleLayerId = computed(() => {
  if (!isMultiLayer.value) return null
  let last: string | null = null
  for (const layer of availableLayers.value) {
    if (visibleLayerIds.value.has(layer.id)) {
      last = layer.id
    }
  }
  return last
})

watch(
  () => props.views,
  (views) => {
    if (!views.length) {
      activeViewId.value = null
      return
    }

    if (activeViewId.value && views.some((view) => view.id === activeViewId.value)) {
      return
    }

    const preferredId = props.initialViewId && views.some((view) => view.id === props.initialViewId)
      ? props.initialViewId
      : views[0]?.id ?? null
    activeViewId.value = preferredId
  },
  { immediate: true },
)

watch(activeViewId, (value, _old) => {
  if (!value) return
  emit("viewChange", value)
  resetView()
})

watch(
  () => activeView.value,
  (view) => {
    if (view?.layers?.length) {
      const defaults = view.layers.filter((l) =>
        l.id === "front" || l.id === "back" || l.id === "pcb-top" || l.id === "pcb-bottom"
      ).map((l) => l.id)


      if (defaults.length === 0 && view.layers.length > 0) {
        defaults.push(view.layers[0].id)
      }
      visibleLayerIds.value = new Set(defaults)
    } else {
      visibleLayerIds.value = new Set()
    }
  },
  { immediate: true }
)

watch(
  () => displayAsset.value?.url,
  () => {
    if (isMultiLayer.value) return // Handled by layer loading
    assetError.value = null
    isAssetLoaded.value = false
    nextTick(() => {
      resetView(true)
      updateAssetBounds()
    })
  },
)

watch([zoom, () => translate.value.x, () => translate.value.y], () => {
  nextTick(() => {
    updateAssetBounds()
  })
})

onMounted(() => {
  window.addEventListener("resize", updateAssetBounds)
})

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateAssetBounds)
})

function setActiveView(viewId: string) {
  if (activeViewId.value === viewId) return
  activeViewId.value = viewId
}

function adjustZoom(direction: 1 | -1) {
  const nextZoom = Number((zoom.value + direction * zoomStep).toFixed(2))
  zoom.value = Math.min(maxZoom, Math.max(minZoom, nextZoom))
  updateAssetBounds()
}

function resetView(skipZoomReset = false) {
  if (!skipZoomReset) zoom.value = computeInitialZoom()
  translate.value = { x: 0, y: 0 }
  nextTick(() => updateAssetBounds())
}

function flipModelOrientation() {
  modelViewerRef.value?.toggleFlip()
}

function computeInitialZoom() {
  if (!contentRef.value || !imageRef.value) return 1

  const { width: viewportWidth, height: viewportHeight } = contentRef.value.getBoundingClientRect()
  if (!viewportWidth || !viewportHeight) return 1

  const naturalWidth = imageRef.value.naturalWidth || imageRef.value.width
  const naturalHeight = imageRef.value.naturalHeight || imageRef.value.height
  if (!naturalWidth || !naturalHeight) return 1

  const isMobile = window.innerWidth < 768
  const fillFactor = isMobile ? 2.5 : defaultViewportFill

  const widthScale = (viewportWidth * fillFactor) / naturalWidth
  const heightScale = (viewportHeight * fillFactor) / naturalHeight

  const scale = isMobile ? widthScale : Math.min(widthScale, heightScale)

  if (!Number.isFinite(scale) || scale <= 0) return 1

  const clamped = Math.min(maxZoom, Math.max(minZoom, scale))
  return Number(clamped.toFixed(2))
}

function handleWheel(event: WheelEvent) {
  if (!contentRef.value || props.interactionMode !== "pan") return
  event.preventDefault()

  const delta = Math.sign(event.deltaY)
  adjustZoom(delta > 0 ? -1 : 1)
}

function handlePointerDown(event: PointerEvent) {
  if (props.interactionMode !== "pan") return
  if (event.pointerType === "touch") event.preventDefault()
  if (!contentRef.value || isPanning.value) return

  isPanning.value = true
  activePointerId.value = event.pointerId
  pointerStart.value = { x: event.clientX, y: event.clientY }
  panOrigin.value = { ...translate.value }
  contentRef.value.setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (props.interactionMode !== "pan") return
  if (!isPanning.value || activePointerId.value !== event.pointerId) return
  event.preventDefault()

  const deltaX = event.clientX - pointerStart.value.x
  const deltaY = event.clientY - pointerStart.value.y

  translate.value = {
    x: panOrigin.value.x + deltaX,
    y: panOrigin.value.y + deltaY,
  }
}

function handlePointerUp(event: PointerEvent) {
  if (props.interactionMode !== "pan") return
  if (!isPanning.value || activePointerId.value !== event.pointerId) return

  isPanning.value = false
  activePointerId.value = null
  contentRef.value?.releasePointerCapture(event.pointerId)
}

function handlePointerLeave(event: PointerEvent) {
  if (props.interactionMode !== "pan") return
  if (!isPanning.value || activePointerId.value !== event.pointerId) return
  handlePointerUp(event)
}

function handleAssetLoad() {
  isAssetLoaded.value = true
  zoom.value = computeInitialZoom()
  nextTick(() => updateAssetBounds())
}

function handleAssetError() {
  if (!isMultiLayer.value) {
    assetError.value = "Failed to load asset"
  }
}

function handleCanvasClick(event: MouseEvent) {
  if (props.interactionMode !== "pin") return
  if (!imageRef.value || !activeView.value) return

  const rect = assetBounds.value ?? imageRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) return

  const relativeX = (event.clientX - rect.left) / rect.width
  const relativeY = (event.clientY - rect.top) / rect.height

  if (relativeX < 0 || relativeX > 1 || relativeY < 0 || relativeY > 1) {
    return
  }

  emit("canvasClick", {
    viewId: activeView.value.id,
    relativeX,
    relativeY,
    clientX: event.clientX,
    clientY: event.clientY,
  })
}

function updateAssetBounds() {
  if (is3DView.value) {
    if (modelBounds.value) {
      assetBounds.value = new DOMRect(
        modelBounds.value.x,
        modelBounds.value.y,
        modelBounds.value.width,
        modelBounds.value.height,
      )
    } else {
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

function handleModelBounds(rect: DOMRect) {
  modelBounds.value = rect
  if (is3DView.value) {
    assetBounds.value = new DOMRect(rect.x, rect.y, rect.width, rect.height)
  }
}

function toggleLayer(layerId: string, visible: boolean) {
  const next = new Set(visibleLayerIds.value)
  if (visible) {
    next.add(layerId)
  } else {
    next.delete(layerId)
  }
  visibleLayerIds.value = next
}

defineExpose({ adjustZoom, resetView })
</script>

<template>
  <div class="space-y-4">
    <div v-if="showControlsBar" class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <Button v-for="view in views" :key="view.id" variant="regular" size="sm" class="px-4 text-sm transition" :class="view.id === activeView?.id
          ? 'bg-cs-dark-green border-cs-dark-green text-white'
          : 'bg-cs-lighter-green text-cs-charcoal border-cs-whiteish hover:bg-cs-light-green hover:text-white'"
          @click="setActiveView(view.id)">
          {{ view.label }}
        </Button>
      </div>
      <div class="flex items-center gap-2">
        <template v-if="showZoomControls">
          <Button size="sm" variant="regular" class="h-8 w-8 p-0" @click="adjustZoom(-1)">
            <span class="text-lg leading-none">−</span>
          </Button>
          <Button size="sm" variant="regular" class="h-8 w-8 p-0" @click="adjustZoom(1)">
            <span class="text-lg leading-none">+</span>
          </Button>
          <Button size="sm" variant="regular" class="h-8 px-3" @click="resetView()">
            Reset
          </Button>
        </template>
        <Button v-if="canFlipModel" size="sm" variant="regular" class="h-8 px-3" @click="flipModelOrientation">
          Flip view
        </Button>
      </div>
    </div>

    <div ref="containerRef" class="relative overflow-hidden rounded-lg">
      <div v-if="!views.length" class="flex h-[520px] items-center justify-center text-sm text-muted-foreground">
        No views available.
      </div>
      <template v-else>
        <div v-if="is3DView" class="relative h-[520px] select-none">
          <ProjectModelViewer ref="modelViewerRef" class="h-full w-full" :model-url="activeAsset?.url || undefined"
            @bounds-change="handleModelBounds" />
          <div v-if="!activeAsset?.url"
            class="absolute inset-0 flex items-center justify-center rounded-lg border border-dashed border-muted-foreground/40 bg-muted/20 p-6 text-sm text-muted-foreground">
            {{ activeView?.fallbackMessage ?? "No 3D model available." }}
          </div>
        </div>
        <div v-else ref="contentRef" class="relative h-[520px] touch-none select-none"
          :class="has2DAsset ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'" :style="layoutBackgroundStyle"
          @wheel.prevent="handleWheel" @pointerdown="handlePointerDown" @pointermove="handlePointerMove"
          @pointerup="handlePointerUp" @pointercancel="handlePointerUp" @pointerleave="handlePointerLeave"
          @dblclick.prevent="resetView()" @click="handleCanvasClick">
          <div
            class="absolute left-1/2 top-1/2 flex h-full w-full -translate-x-1/2 -translate-y-1/2 items-center justify-center">
            <div class="transition-transform duration-75 ease-out" :style="{
              transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})`,
            }">
              <div class="relative flex items-center justify-center">
                <div v-if="!has2DAsset"
                  class="flex h-[420px] w-[720px] max-w-[85vw] flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-muted-foreground/40 p-6 text-center text-sm text-muted-foreground">
                  <p>{{ assetError ?? activeView?.fallbackMessage ?? "No asset available for this view." }}</p>
                </div>

                <div v-else class="relative max-h-[70vh] max-w-[80vw]" :style="layoutBackgroundStyle">
                  <template v-if="isMultiLayer">
                    <template v-for="(layer, index) in availableLayers" :key="layer.id">
                      <img v-if="visibleLayerIds.has(layer.id)" :src="layer.url || ''" :alt="layer.title"
                        draggable="false" @dragstart.prevent loading="lazy" decoding="async"
                        class="max-h-[70vh] max-w-[80vw] transition-opacity duration-200"
                        :class="layer.id === firstVisibleLayerId ? 'relative' : 'absolute left-0 top-0'" :style="{
                          zIndex: availableLayers.length - index,
                          opacity: (visibleLayerIds.size > 1 && layer.id !== bottomVisibleLayerId) ? 0.8 : 1,
                          mixBlendMode: visibleLayerIds.size > 1 ? 'screen' : 'normal'
                        }"
                        :ref="(el) => { if (layer.id === firstVisibleLayerId || (visibleLayerIds.has(layer.id) && !imageRef)) imageRef = el as HTMLImageElement }"
                        @load="handleAssetLoad" @error="handleAssetError" />
                    </template>
                  </template>
                  <template v-else>
                    <img ref="imageRef" :key="displayAssetKey" :src="displayAssetSrc" :alt="displayAssetAlt"
                      draggable="false" @dragstart.prevent loading="lazy" decoding="async"
                      class="max-h-[70vh] max-w-[80vw]" @load="handleAssetLoad" @error="handleAssetError" />
                  </template>
                  <div v-if="!isAssetLoaded && !isMultiLayer" class="absolute inset-0" />
                  <div class="pointer-events-none absolute inset-0" :style="{ zIndex: 100 }">
                    <slot name="overlay" :view="activeView" :asset="displayAsset" :image-bounds="assetBounds" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="isMultiLayer"
            class="absolute right-4 top-4 z-20 rounded-lg border border-white bg-cs-lighter-green p-3 shadow-sm backdrop-blur text-cs-charcoal"
            @pointerdown.stop @dblclick.stop>
            <h4 class="mb-2 text-xs font-semibold text-cs-charcoal">Layers</h4>
            <div class="flex flex-col gap-2">
              <div v-for="layer in availableLayers" :key="layer.id" class="flex items-center gap-2">
                <Checkbox :id="`layer-${layer.id}`" :model-value="visibleLayerIds.has(layer.id)" :class="visibleLayerIds.has(layer.id)
                  ? 'bg-cs-dark-green border-cs-dark-green text-white'
                  : 'bg-white/10 border-white/60'"
                  @update:model-value="(val: boolean) => toggleLayer(layer.id, val)" />
                <Label :for="`layer-${layer.id}`" class="text-xs cursor-pointer select-none text-cs-charcoal">
                  {{ layer.title }}
                </Label>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.touch-none {
  touch-action: none;
}
</style>
