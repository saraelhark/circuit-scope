<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import { Button } from "~/components/ui/button"
import type { PreviewAsset } from "~/types/api/projects"

export type ViewerView = {
  id: string
  label: string
  asset?: PreviewAsset | null
  fallbackMessage?: string
}

const props = withDefaults(
  defineProps<{
    views: ViewerView[]
    initialViewId?: string
    interactionMode?: "pan" | "pin"
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

const defaultViewportFill = 0.7

const panOrigin = ref({ x: 0, y: 0 })
const pointerStart = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const activePointerId = ref<number | null>(null)

const contentRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

const isAssetLoaded = ref(false)
const assetError = ref<string | null>(null)
const assetBounds = ref<DOMRect | null>(null)

const activeView = computed(() => props.views.find((view) => view.id === activeViewId.value) ?? props.views[0])
const activeAsset = computed(() => activeView.value?.asset)

const hasAsset = computed(() => Boolean(activeAsset.value?.url && !activeAsset.value.placeholder && !assetError.value))
const isLayoutView = computed(() => activeView.value?.id?.startsWith("pcb"))
const layoutBackgroundStyle = computed(() => (isLayoutView.value ? { backgroundColor: "#001124" } : undefined))

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

watch(activeViewId, (value) => {
  if (!value) return
  emit("viewChange", value)
  resetView()
})

watch(
  () => activeAsset.value?.url,
  () => {
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

function computeInitialZoom() {
  if (!contentRef.value || !imageRef.value) return 1

  const { width: viewportWidth, height: viewportHeight } = contentRef.value.getBoundingClientRect()
  if (!viewportWidth || !viewportHeight) return 1

  const naturalWidth = imageRef.value.naturalWidth || imageRef.value.width
  const naturalHeight = imageRef.value.naturalHeight || imageRef.value.height
  if (!naturalWidth || !naturalHeight) return 1

  const widthScale = (viewportWidth * defaultViewportFill) / naturalWidth
  const heightScale = (viewportHeight * defaultViewportFill) / naturalHeight
  const scale = Math.min(widthScale, heightScale)

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
  assetError.value = "Failed to load asset"
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
  if (!imageRef.value) {
    assetBounds.value = null
    return
  }
  const rect = imageRef.value.getBoundingClientRect()
  assetBounds.value = new DOMRect(rect.x, rect.y, rect.width, rect.height)
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-2">
        <button v-for="view in views" :key="view.id" type="button"
          class="rounded-md border px-3 py-1 text-sm transition" :class="view.id === activeView?.id
            ? 'border-primary bg-primary/10 text-primary'
            : 'border-border text-muted-foreground hover:bg-muted'" @click="setActiveView(view.id)">
          {{ view.label }}
        </button>
      </div>
      <div class="flex items-center gap-2">
        <Button size="sm" variant="outline" @click="adjustZoom(-1)">
          −
        </Button>
        <span class="text-xs tabular-nums text-muted-foreground">{{ Math.round(zoom * 100) }}%</span>
        <Button size="sm" variant="outline" @click="adjustZoom(1)">
          +
        </Button>
        <Button size="sm" variant="secondary" @click="resetView()">
          Reset
        </Button>
      </div>
    </div>

    <div ref="containerRef" class="relative overflow-hidden rounded-lg border bg-background">
      <div v-if="!views.length" class="flex h-[520px] items-center justify-center text-sm text-muted-foreground">
        No views available.
      </div>
      <template v-else>
        <div ref="contentRef" class="relative h-[520px] touch-none select-none" :class="hasAsset ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'
          " :style="layoutBackgroundStyle" @wheel.prevent="handleWheel" @pointerdown="handlePointerDown"
          @pointermove="handlePointerMove" @pointerup="handlePointerUp" @pointercancel="handlePointerUp"
          @pointerleave="handlePointerLeave" @dblclick.prevent="resetView()" @click="handleCanvasClick">
          <div
            class="absolute left-1/2 top-1/2 flex h-full w-full -translate-x-1/2 -translate-y-1/2 items-center justify-center">
            <div class="transition-transform duration-75 ease-out" :style="{
              transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})`,
            }">
              <div class="relative flex items-center justify-center">
                <div v-if="!hasAsset"
                  class="flex h-[420px] w-[720px] max-w-[85vw] flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-muted-foreground/40 bg-muted/20 p-6 text-center text-sm text-muted-foreground">
                  <p>{{ assetError ?? activeView?.fallbackMessage ?? "No asset available for this view." }}</p>
                  <p v-if="activeAsset?.placeholder" class="text-xs text-muted-foreground">
                    Placeholder generated during processing.
                  </p>
                </div>

                <div v-else class="relative max-h-[70vh] max-w-[80vw]" :style="layoutBackgroundStyle">
                  <img ref="imageRef" :key="activeAsset?.url ?? activeAsset?.path" :src="activeAsset?.url ?? ''"
                    :alt="activeAsset?.title ?? activeAsset?.filename ?? 'Preview asset'" draggable="false"
                    @dragstart.prevent loading="lazy" decoding="async" class="max-h-[70vh] max-w-[80vw]"
                    @load="handleAssetLoad" @error="handleAssetError" />
                  <div v-if="!isAssetLoaded" class="absolute inset-0 animate-pulse bg-muted/50" />
                  <div class="pointer-events-none absolute inset-0">
                    <slot name="overlay" :view="activeView" :asset="activeAsset" :image-bounds="assetBounds" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
      <div class="space-x-2">
        <span>{{ activeView?.label ?? "View" }}</span>
        <span v-if="activeAsset?.title">• {{ activeAsset.title }}</span>
        <span v-if="activeAsset?.page !== undefined">• Page {{ activeAsset.page }}</span>
        <span v-if="activeAsset?.layers?.length">• Layers: {{ activeAsset.layers.join(", ") }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.touch-none {
  touch-action: none;
}
</style>
