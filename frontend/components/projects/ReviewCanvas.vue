<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { Checkbox } from "~/components/ui/checkbox"
import { Label } from "~/components/ui/label"
import { useCanvasInteraction } from "~/composables/useCanvasInteraction"
import CanvasOverlays from "~/components/projects/CanvasOverlays.vue"
import CommentIcon from "~/components/projects/CommentIcon.vue"
import ProjectModelViewer from "~/components/projects/ProjectModelViewer.vue"
import type { ViewerView } from "~/types/viewer"
import type { CommentThread } from "~/types/api/commentThreads"

export type PinViewerAnnotation = {
    id: string
    tool: "pin"
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
        views: ViewerView[]
        initialViewId?: string
        activeTool: "pan" | "pin"
        annotations?: Record<string, ViewerAnnotation[]>
        highlightedThreadId?: string | null
        pendingPin?: { x: number; y: number } | null
        activeThread?: CommentThread | null
        currentUserInitial?: string
        canResolveThreads?: boolean
        authorColorMap?: Map<string, string>
        currentUserColor?: string
    }>(),
    {
        views: () => [],
        activeTool: "pan",
        annotations: () => ({}),
        highlightedThreadId: null,
        pendingPin: null,
        activeThread: null,
        currentUserInitial: "G",
        canResolveThreads: false,
        currentUserColor: "#FFD02B",
    },
)

const emit = defineEmits<{
    viewChange: [viewId: string]
    pinCreated: [
        {
            viewId: string
            pinX: number
            pinY: number
            tool: "pin"
            data: { initial: string; comment: string; authorName: string }
        }
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
const activeView = computed(() => props.views.find((v) => v.id === activeViewId.value) ?? props.views[0])
const composedAsset = computed(() => activeView.value?.asset ?? null)
const activeAsset = computed(() => composedAsset.value ?? activeView.value?.asset)

const availableLayers = computed(() => activeView.value?.layers ?? [])
const isMultiLayer = computed(() => availableLayers.value.length > 0)
const visibleLayerIds = ref<Set<string>>(new Set())

const is3DView = computed(() => activeView.value?.kind === "3d")
const isLayoutView = computed(() => !is3DView.value && (activeView.value?.id?.startsWith("pcb") || isMultiLayer.value))
const layoutBackgroundStyle = computed(() => (isLayoutView.value ? { backgroundColor: "#001124" } : undefined))

const disablePan = computed(() => props.activeTool !== "pan" || is3DView.value)

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
    handlePointerMove
} = useCanvasInteraction(contentRef, { disableInteraction: disablePan })

function handleCombinedPointerMove(e: PointerEvent) {
    handleCursorMove(e)
    handlePointerMove(e)
}

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

function resetView() {
    resetTranslate()
    const initialZoom = computeInitialZoom()
    setZoom(initialZoom)
    nextTick(() => updateAssetBounds())
}

function computeInitialZoom() {
    if (!contentRef.value || !imageRef.value) return 1
    const viewport = contentRef.value.getBoundingClientRect()
    const natW = imageRef.value.naturalWidth || imageRef.value.width
    const natH = imageRef.value.naturalHeight || imageRef.value.height
    if (!natW || !natH) return 1
    const scale = Math.min((viewport.width * 0.9) / natW, (viewport.height * 0.9) / natH)
    const clamped = Math.min(6, Math.max(0.25, scale))
    return Number(clamped.toFixed(2))
}

function handlePointerUp(event: PointerEvent) {
    if (props.activeTool === "pan") {
        stopPanning(event)
    }
}


const activeViewPins = computed(() => {
    const viewId = activeView.value?.id
    if (!viewId) return []
    return props.annotations?.[viewId] ?? []
})

function canvasPointerDown(e: PointerEvent) {
    if (props.activeTool !== "pin") return

    const target = e.target as HTMLElement
    if (target.closest('.pointer-events-auto')) return

    e.preventDefault()

    if (props.pendingPin) {
        emit("cancelComment")
        return
    }

    updateAssetBounds()
    if (!assetBounds.value) return

    const rel = clientToRelative(e.clientX, e.clientY)

    emit("pinCreated", {
        viewId: activeView.value.id,
        tool: "pin",
        pinX: rel.x,
        pinY: rel.y,
        data: { initial: props.currentUserInitial, comment: "", authorName: "Me" }
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

function handleImageLoad() {
    zoom.value = computeInitialZoom()
    nextTick(() => updateAssetBounds())
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

function toggleLayer(layerId: string, visible: boolean) {
    const next = new Set(visibleLayerIds.value)
    if (visible) {
        next.add(layerId)
    } else {
        next.delete(layerId)
    }
    visibleLayerIds.value = next
}

const cursorX = ref(0)
const cursorY = ref(0)
const cursorVisible = ref(false)

function handleCursorMove(e: PointerEvent) {
    if (props.activeTool !== 'pin') return
    cursorX.value = e.clientX
    cursorY.value = e.clientY
}

onMounted(() => {
    window.addEventListener("resize", updateAssetBounds)
})
onBeforeUnmount(() => {
    window.removeEventListener("resize", updateAssetBounds)
})

defineExpose({ adjustZoom, resetView, setActiveView, flipModel: flipModelOrientation })
</script>

<template>
    <div class="relative h-full w-full">
        <div v-if="is3DView" class="relative h-full w-full">
            <ProjectModelViewer ref="modelViewerRef" :model-url="activeAsset?.url || undefined"
                :interaction-enabled="false" @bounds-change="handleModelBounds" />
            <div v-if="!activeAsset?.url"
                class="absolute inset-0 flex h-full w-full items-center justify-center border border-dashed border-muted-foreground/40 bg-muted/20 p-6 text-sm text-muted-foreground">
                {{ activeView?.fallbackMessage ?? 'No 3D model available.' }}
            </div>

            <div class="absolute inset-0" :class="props.activeTool === 'pin' ? 'cursor-none' : ''"
                @pointermove="handleCursorMove" @pointerleave="cursorVisible = false"
                @pointerenter="cursorVisible = true" @pointerdown.capture="canvasPointerDown">

                <div v-if="props.activeTool === 'pin' && cursorVisible"
                    class="pointer-events-none fixed z-[9999] drop-shadow-md"
                    :style="{ left: `${cursorX}px`, top: `${cursorY}px`, transform: 'translate(-0%, -100%)' }">
                    <CommentIcon :initial="currentUserInitial" size="lg" :color="currentUserColor" />
                </div>

                <CanvasOverlays v-if="assetBounds" :pins="activeViewPins" :active-thread-id="activeThread?.id"
                    :zoom="zoom" :pending-pin="pendingPin"
                    :active-thread="activeThread && activeThread.view_id === activeView.id ? activeThread : null"
                    :current-user-initial="currentUserInitial" :author-color-map="authorColorMap"
                    :current-user-color="currentUserColor" @pin-hover="(id: string) => emit('pinHover', id)"
                    @pin-leave="(id: string) => emit('pinLeave', id)" @pin-click="(id: string) => emit('pinClick', id)"
                    @submit-comment="(content: string) => emit('submitComment', content)"
                    @cancel-comment="emit('cancelComment')" @reply="(content: string) => emit('submitReply', content)"
                    @resolve-thread="(thread: CommentThread) => emit('resolveThread', thread)"
                    @close-thread="emit('closeThread')" />
            </div>
        </div>

        <div v-else ref="contentRef" class="relative h-full w-full touch-none select-none"
            :style="{ cursor: props.activeTool === 'pan' ? (isPanning ? 'grabbing' : 'grab') : 'default', backgroundColor: layoutBackgroundStyle?.backgroundColor ?? 'transparent' }"
            :class="props.activeTool === 'pin' ? 'cursor-none' : ''" @wheel.prevent="handleWheel"
            @pointerdown="handlePointerDown" @pointercancel="stopPanning"
            @pointerleave="stopPanning; cursorVisible = false" @dblclick.prevent="resetView()"
            @pointerdown.capture="canvasPointerDown" @pointerup="handlePointerUp"
            @pointermove="handleCombinedPointerMove" @pointerenter="cursorVisible = true">

            <div v-if="props.activeTool === 'pin' && cursorVisible"
                class="pointer-events-none fixed z-[9999] drop-shadow-md"
                :style="{ left: `${cursorX}px`, top: `${cursorY}px`, transform: 'translate(-0%, -100%)' }">
                <CommentIcon :initial="currentUserInitial" size="lg" :color="currentUserColor" />
            </div>

            <div class="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2" style="user-select: none;">
                <div class="transition-transform duration-75 ease-out"
                    :style="{ transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})` }">
                    <div class="relative flex items-center justify-center">

                        <div v-if="isMultiLayer" class="relative max-h-[70vh] max-w-[80vw]">
                            <template v-for="(layer, index) in availableLayers" :key="layer.id">
                                <img v-if="visibleLayerIds.has(layer.id)" :src="layer.url || ''" :alt="layer.title"
                                    draggable="false" @dragstart.prevent loading="lazy" decoding="async"
                                    class="max-h-[70vh] max-w-[80vw] transition-opacity duration-200"
                                    :class="layer.id === firstVisibleLayerId ? 'relative' : 'absolute left-0 top-0'"
                                    :style="{
                                        zIndex: availableLayers.length - index,
                                        opacity: (visibleLayerIds.size > 1 && layer.id !== bottomVisibleLayerId) ? 0.8 : 1,
                                        mixBlendMode: visibleLayerIds.size > 1 ? 'screen' : 'normal'
                                    }"
                                    :ref="(el) => { if (layer.id === firstVisibleLayerId || (visibleLayerIds.has(layer.id) && !imageRef)) imageRef = el as HTMLImageElement }"
                                    @load="handleImageLoad" />
                            </template>

                            <CanvasOverlays v-if="assetBounds" :pins="activeViewPins"
                                :active-thread-id="activeThread?.id" :zoom="zoom" :pending-pin="pendingPin"
                                :active-thread="activeThread && activeThread.view_id === activeView.id ? activeThread : null"
                                :current-user-initial="currentUserInitial" :author-color-map="authorColorMap"
                                :current-user-color="currentUserColor" @pin-hover="(id: string) => emit('pinHover', id)"
                                @pin-leave="(id: string) => emit('pinLeave', id)"
                                @pin-click="(id: string) => emit('pinClick', id)"
                                @submit-comment="(content: string) => emit('submitComment', content)"
                                @cancel-comment="emit('cancelComment')"
                                @reply="(content: string) => emit('submitReply', content)"
                                @resolve-thread="(thread: CommentThread) => emit('resolveThread', thread)"
                                @close-thread="emit('closeThread')" />
                        </div>

                        <div v-else-if="activeAsset?.url" class="relative">
                            <img ref="imageRef" :src="activeAsset.url" :alt="activeAsset.title ?? 'Preview asset'"
                                draggable="false" @dragstart.prevent loading="lazy" decoding="async"
                                @load="handleImageLoad" class="max-h-[70vh] max-w-[80vw]" />

                            <CanvasOverlays v-if="assetBounds" :pins="activeViewPins"
                                :active-thread-id="activeThread?.id" :zoom="zoom" :pending-pin="pendingPin"
                                :active-thread="activeThread && activeThread.view_id === activeView.id ? activeThread : null"
                                :current-user-initial="currentUserInitial" :author-color-map="authorColorMap"
                                :current-user-color="currentUserColor" @pin-hover="(id: string) => emit('pinHover', id)"
                                @pin-leave="(id: string) => emit('pinLeave', id)"
                                @pin-click="(id: string) => emit('pinClick', id)"
                                @submit-comment="(content: string) => emit('submitComment', content)"
                                @cancel-comment="emit('cancelComment')"
                                @reply="(content: string) => emit('submitReply', content)"
                                @resolve-thread="(thread: CommentThread) => emit('resolveThread', thread)"
                                @close-thread="emit('closeThread')" />
                        </div>

                        <div v-else
                            class="flex h-[420px] w-[720px] max-w-[85vw] items-center justify-center border border-dashed border-muted-foreground/40 bg-muted/20 p-6 text-sm text-muted-foreground">
                            {{ activeView?.fallbackMessage ?? 'No asset available.' }}
                        </div>
                    </div>
                </div>
            </div>

            <div v-if="isMultiLayer"
                class="absolute right-4 top-4 z-20 rounded-md border bg-card/90 p-3 shadow-sm backdrop-blur"
                @pointerdown.stop @dblclick.stop>
                <h4 class="mb-2 text-xs font-semibold text-muted-foreground">Layers</h4>
                <div class="flex flex-col gap-2">
                    <div v-for="layer in availableLayers" :key="layer.id" class="flex items-center gap-2">
                        <Checkbox :id="`layer-${layer.id}`" :model-value="visibleLayerIds.has(layer.id)"
                            @update:model-value="(val: boolean) => toggleLayer(layer.id, val)" />
                        <Label :for="`layer-${layer.id}`" class="text-xs cursor-pointer select-none">{{ layer.title
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
