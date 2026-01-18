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
  options: CanvasInteractionOptions = {},
) {
  const zoom = ref(options.initialZoom ?? 1)
  const translate = ref({ x: 0, y: 0 })

  const isPanning = ref(false)
  const panOrigin = ref({ x: 0, y: 0 })
  const pointerStart = ref({ x: 0, y: 0 })
  const activePointerId = ref<number | null>(null)

  const pointers = new Map<number, PointerEvent>()
  let lastPinchDistance = 0
  let lastPinchCenter = { x: 0, y: 0 }
  let isPinching = false

  const minZoom = options.minZoom ?? 0.1
  const maxZoom = options.maxZoom ?? 20
  const zoomStep = options.zoomStep ?? 0.25

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

  function getPinchDistance(): number {
    const pts = Array.from(pointers.values())
    if (pts.length < 2) return 0
    const dx = pts[1].clientX - pts[0].clientX
    const dy = pts[1].clientY - pts[0].clientY
    return Math.sqrt(dx * dx + dy * dy)
  }

  function getPinchCenter(): { x: number, y: number } {
    const pts = Array.from(pointers.values())
    if (pts.length < 2) return { x: 0, y: 0 }
    return {
      x: (pts[0].clientX + pts[1].clientX) / 2,
      y: (pts[0].clientY + pts[1].clientY) / 2,
    }
  }

  function handlePointerDown(event: PointerEvent) {
    if (options.disableInteraction?.value) return
    if (event.pointerType === 'touch') event.preventDefault()
    if (!contentRef.value) return

    pointers.set(event.pointerId, event)

    if (pointers.size === 2) {
      isPinching = true
      isPanning.value = false
      lastPinchDistance = getPinchDistance()
      lastPinchCenter = getPinchCenter()
      panOrigin.value = { ...translate.value }
    }
    else if (pointers.size === 1 && !isPanning.value) {
      isPanning.value = true
      activePointerId.value = event.pointerId
      pointerStart.value = { x: event.clientX, y: event.clientY }
      panOrigin.value = { ...translate.value }
      contentRef.value.setPointerCapture(event.pointerId)
    }
  }

  function handlePointerMove(event: PointerEvent) {
    if (options.disableInteraction?.value) return

    pointers.set(event.pointerId, event)

    if (isPinching && pointers.size === 2) {
      event.preventDefault()
      const newDistance = getPinchDistance()
      const newCenter = getPinchCenter()

      if (lastPinchDistance > 0) {
        const scale = newDistance / lastPinchDistance
        const newZoom = zoom.value * scale
        setZoom(newZoom)
      }

      const dx = newCenter.x - lastPinchCenter.x
      const dy = newCenter.y - lastPinchCenter.y
      translate.value = {
        x: translate.value.x + dx,
        y: translate.value.y + dy,
      }

      lastPinchDistance = newDistance
      lastPinchCenter = newCenter
    }
    else if (isPanning.value && activePointerId.value === event.pointerId && pointers.size === 1) {
      event.preventDefault()
      const dx = event.clientX - pointerStart.value.x
      const dy = event.clientY - pointerStart.value.y
      translate.value = { x: panOrigin.value.x + dx, y: panOrigin.value.y + dy }
    }
  }

  function stopPanning(event: PointerEvent) {
    pointers.delete(event.pointerId)

    if (pointers.size < 2) {
      isPinching = false
      lastPinchDistance = 0
    }

    if (pointers.size === 0) {
      isPanning.value = false
      activePointerId.value = null
    }
    else if (pointers.size === 1 && !isPinching) {
      const remainingPointer = Array.from(pointers.values())[0]
      activePointerId.value = remainingPointer.pointerId
      pointerStart.value = { x: remainingPointer.clientX, y: remainingPointer.clientY }
      panOrigin.value = { ...translate.value }
      isPanning.value = true
    }

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
    stopPanning,
  }
}
