<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import type { PreviewAsset } from "~/types/api/projects"

export type ViewerView = {
  id: string
  label: string
  asset?: PreviewAsset | null
  fallbackMessage?: string
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

export type ArrowViewerAnnotation = {
  id: string
  tool: "arrow"
  pinX: number
  pinY: number
  data: {
    target_x: number
    target_y: number
  }
}

export type ViewerAnnotation = CircleViewerAnnotation | ArrowViewerAnnotation

const props = withDefaults(
  defineProps<{
    views: ViewerView[]
    initialViewId?: string
    /* Currently active tool chosen in the toolbar */
    activeTool: "pan" | "circle" | "arrow"
    annotations?: Record<string, ViewerAnnotation[]>
  }>(),
  {
    views: () => [],
    activeTool: "pan",
    annotations: () => ({}),
  },
)

const emit = defineEmits<{
  /** Notifies parent when the current view (schematic / pcb) changes */
  viewChange: [viewId: string]
  /** Emitted once a drawing gesture finishes (pointer up) */
  shapeCreated: [
    (
      | ({
          viewId: string
          /** pinX / pinY are the anchor point (centre for circle, start for arrow) in 0..1 percentages */
          pinX: number
          pinY: number
        } & CircleViewerAnnotation)
      | ({
          viewId: string
          pinX: number
          pinY: number
        } & ArrowViewerAnnotation)
    )
  ]
}>()

/* ------------------------------------------------------------------
 * Internal state – zoom / pan (lifted from ProjectAssetViewer)
 * ---------------------------------------------------------------- */
const zoom = ref(1)
const minZoom = 0.25
const maxZoom = 6
const zoomStep = 0.2
const translate = ref({ x: 0, y: 0 })
/* Store for gesture-based panning */
const panOrigin = ref({ x: 0, y: 0 })
const pointerStart = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const activePointerId = ref<number | null>(null)

/* Refs to the container & image used for sizing */
const contentRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

/* Keep a DOMRect of the current rendered asset – required to translate
   between client coordinates and relative 0..1 positions */
const assetBounds = ref<DOMRect | null>(null)

/* Active view logic */
const activeViewId = ref<string | null>(null)
const activeView = computed(() => props.views.find((v) => v.id === activeViewId.value) ?? props.views[0])
const activeAsset = computed(() => activeView.value?.asset)
const isLayoutView = computed(() => activeView.value?.id?.startsWith("pcb"))
const layoutBackgroundStyle = computed(() => (isLayoutView.value ? { backgroundColor: "#001124" } : undefined))
const annotationColor = "#7CFF00"

function setActiveView(viewId: string) {
  if (activeViewId.value === viewId) return
  if (!props.views.some((view) => view.id === viewId)) return
  activeViewId.value = viewId
}

/* Detect the preferred initial view once props.views is populated */
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

/* ------------------------------------------------------------------
 * Zoom helpers – called from parent via exposed methods
 * ---------------------------------------------------------------- */
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
  const scale = Math.min((viewport.width * 0.7) / natW, (viewport.height * 0.7) / natH)
  const clamped = Math.min(maxZoom, Math.max(minZoom, scale))
  return Number(clamped.toFixed(2))
}

/* ------------------------------------------------------------------
 * Panning handlers
 * ---------------------------------------------------------------- */
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

/* ------------------------------------------------------------------
 * Wheel zoom
 * ---------------------------------------------------------------- */
function handleWheel(e: WheelEvent) {
  if (props.activeTool !== "pan") return // Keep standard behaviour while drawing
  e.preventDefault()
  const delta = Math.sign(e.deltaY)
  adjustZoom(delta > 0 ? -1 : 1)
}

/* ------------------------------------------------------------------
 * Drawing (circle / arrow)
 * ---------------------------------------------------------------- */
type DraftShape = { tool: "circle" | "arrow"; startX: number; startY: number; currentX: number; currentY: number }
type FinalShape = { id: string; tool: "circle" | "arrow"; startX: number; startY: number; endX: number; endY: number }

const draftShape = ref<null | DraftShape>(null)
const shapes = ref<Record<string, FinalShape>>({})

const persistedShapes = computed<Record<string, FinalShape[]>>(() => {
  const result: Record<string, FinalShape[]> = {}
  for (const [viewId, annotations] of Object.entries(props.annotations ?? {})) {
    result[viewId] = annotations
      .map((annotation) => {
        if (annotation.tool === "circle") {
          const radius = Number(annotation.data.radius ?? 0)
          if (!Number.isFinite(radius) || radius <= 0) return null
          const startX = annotation.pinX - radius
          const startY = annotation.pinY - radius
          const endX = annotation.pinX + radius
          const endY = annotation.pinY + radius
          return {
            id: annotation.id,
            tool: "circle" as const,
            startX,
            startY,
            endX,
            endY,
          }
        }
        if (annotation.tool === "arrow") {
          const targetX = Number(annotation.data.target_x)
          const targetY = Number(annotation.data.target_y)
          if (!Number.isFinite(targetX) || !Number.isFinite(targetY)) return null
          return {
            id: annotation.id,
            tool: "arrow" as const,
            startX: annotation.pinX,
            startY: annotation.pinY,
            endX: targetX,
            endY: targetY,
          }
        }
        return null
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
  if (props.activeTool === "pan") return // Pan handled elsewhere
  if (!imageRef.value || !assetBounds.value) return
  e.preventDefault()

  /* Translate client coords → relative 0..1 */
  const rel = clientToRelative(e.clientX, e.clientY)
  draftShape.value = {
    tool: props.activeTool as "circle" | "arrow",
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
  const { tool, startX, startY, currentX, currentY } = draftShape.value
  // Emit shapeCreated event with stabilised data
  if (tool === "circle") {
    /* Circle: centre = midpoint, radius = max(|dx|, |dy|)/2 */
    const centreX = (startX + currentX) / 2
    const centreY = (startY + currentY) / 2
    const radius = Math.max(Math.abs(currentX - startX), Math.abs(currentY - startY)) / 2
    emit("shapeCreated", {
      viewId: activeView.value.id,
      id: "temp",
      tool,
      pinX: centreX,
      pinY: centreY,
      data: { radius: Number(radius.toFixed(4)) },
    })
  } else {
    /* Arrow: start → end */
    emit("shapeCreated", {
      viewId: activeView.value.id,
      id: "temp",
      tool,
      pinX: startX,
      pinY: startY,
      data: { target_x: currentX, target_y: currentY },
    })
  }

  // Push into internal array for preview
  const shape: FinalShape = {
    id: (globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2)),
    tool,
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

/* ------------------------------------------------------------------
 * Asset bounds updates – whenever zoom / pan change or window resizes
 * ---------------------------------------------------------------- */
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

/* Expose methods so parent can control zoom / reset */
defineExpose({ adjustZoom, resetView, setActiveView })
</script>

<template>
  <div class="relative h-full w-full">
    <!-- Main interactive area -->
    <div ref="contentRef" class="relative h-full w-full touch-none select-none"
      :style="{ cursor: props.activeTool === 'pan' ? (isPanning ? 'grabbing' : 'grab') : 'crosshair', backgroundColor: layoutBackgroundStyle?.backgroundColor ?? 'transparent' }"
      @wheel.prevent="handleWheel" @pointerdown="handlePointerDown" @pointercancel="stopPanning"
      @pointerleave="stopPanning" @dblclick.prevent="resetView()" @pointerdown.capture="canvasPointerDown"
      @pointermove.capture="canvasPointerMove" @pointermove="handlePointerMove" @pointerup="handlePointerUp">
      <!-- Centering wrapper so the image stays centred at 0,0 -->
      <div class="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2" style="user-select: none;">
        <div class="transition-transform duration-75 ease-out"
          :style="{ transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})` }">
          <div class="relative flex items-center justify-center">
            <!-- Asset image -->
            <div v-if="activeAsset?.url" class="relative">
              <img ref="imageRef" :src="activeAsset.url" :alt="activeAsset.title ?? 'Preview asset'" draggable="false"
                @dragstart.prevent loading="lazy" decoding="async" @load="handleImageLoad"
                class="max-h-[70vh] max-w-[80vw]" />
              <!-- Overlay SVG for annotations -->
              <svg v-if="assetBounds && (activeViewShapes.length || draftShape)" class="pointer-events-none absolute inset-0"
                :viewBox="`0 0 1 1`" preserveAspectRatio="none" :style="{ overflow: 'visible' }">
                <!-- Render existing shapes -->
                <template v-for="shape in activeViewShapes" :key="shape.id">
                  <circle v-if="shape.tool === 'circle'"
                    :cx="(shape.startX + shape.endX) / 2"
                    :cy="(shape.startY + shape.endY) / 2"
                    :r="Math.max(Math.abs(shape.endX - shape.startX), Math.abs(shape.endY - shape.startY)) / 2"
                    :stroke="annotationColor" stroke-width="0.002" fill="none" />
                  <line v-else :x1="shape.startX" :y1="shape.startY" :x2="shape.endX"
                    :y2="shape.endY" :stroke="annotationColor" stroke-width="0.002"
                    marker-end="url(#arrowhead)" />
                </template>
                <!-- Draft shape while drawing -->
                <template v-if="draftShape">
                  <circle v-if="draftShape.tool === 'circle'" :cx="(draftShape.startX + draftShape.currentX) / 2"
                    :cy="(draftShape.startY + draftShape.currentY) / 2"
                    :r="Math.max(Math.abs(draftShape.currentX - draftShape.startX), Math.abs(draftShape.currentY - draftShape.startY)) / 2"
                    :stroke="annotationColor" stroke-width="0.002" fill="none" stroke-dasharray="0.006" />
                  <line v-else :x1="draftShape.startX" :y1="draftShape.startY" :x2="draftShape.currentX"
                    :y2="draftShape.currentY" :stroke="annotationColor" stroke-width="0.002" stroke-dasharray="0.006" />
                </template>
                <defs>
                  <marker id="arrowhead" markerWidth="0.02" markerHeight="0.02" refX="0.01" refY="0.01" orient="auto"
                    markerUnits="userSpaceOnUse">
                    <path d="M 0 0 L 0 0.02 L 0.02 0.01 Z" :fill="annotationColor" />
                  </marker>
                </defs>
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
