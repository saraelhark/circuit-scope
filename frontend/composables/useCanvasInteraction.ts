import { ref, type Ref } from 'vue'

export interface CanvasInteractionOptions {
    minZoom?: number
    maxZoom?: number
    zoomStep?: number
    initialZoom?: number
    disableInteraction?: Ref<boolean>
}

export function useCanvasInteraction(
    contentRef: Ref<HTMLElement | null>,
    options: CanvasInteractionOptions = {}
) {
    const zoom = ref(options.initialZoom ?? 1)
    const translate = ref({ x: 0, y: 0 })

    const isPanning = ref(false)
    const panOrigin = ref({ x: 0, y: 0 })
    const pointerStart = ref({ x: 0, y: 0 })
    const activePointerId = ref<number | null>(null)

    const minZoom = options.minZoom ?? 0.25
    const maxZoom = options.maxZoom ?? 6
    const zoomStep = options.zoomStep ?? 0.2

    function adjustZoom(direction: 1 | -1) {
        const next = Number((zoom.value + direction * zoomStep).toFixed(2))
        zoom.value = Math.min(maxZoom, Math.max(minZoom, next))
    }

    function setZoom(value: number) {
        const clamped = Math.min(maxZoom, Math.max(minZoom, value))
        zoom.value = Number(clamped.toFixed(2))
    }

    function resetTranslate() {
        translate.value = { x: 0, y: 0 }
    }

    function handleWheel(e: WheelEvent) {
        if (options.disableInteraction?.value) return
        e.preventDefault()
        const delta = Math.sign(e.deltaY)
        adjustZoom(delta > 0 ? -1 : 1)
    }

    function handlePointerDown(event: PointerEvent) {
        if (options.disableInteraction?.value) return
        if (event.pointerType === "touch") event.preventDefault()
        if (!contentRef.value || isPanning.value) return

        isPanning.value = true
        activePointerId.value = event.pointerId
        pointerStart.value = { x: event.clientX, y: event.clientY }
        panOrigin.value = { ...translate.value }
        contentRef.value.setPointerCapture(event.pointerId)
    }

    function handlePointerMove(event: PointerEvent) {
        if (options.disableInteraction?.value) return
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

    return {
        zoom,
        translate,
        isPanning,
        adjustZoom,
        setZoom,
        resetTranslate,
        handleWheel,
        handlePointerDown,
        handlePointerMove,
        stopPanning
    }
}
