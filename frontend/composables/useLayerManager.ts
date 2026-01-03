import { ref, computed, watch, type Ref } from 'vue'
import type { ViewerView } from '~/types/viewer'

export function useLayerManager(activeView: Ref<ViewerView | undefined>) {
  const visibleLayerIds = ref<Set<string>>(new Set())

  const availableLayers = computed(() => activeView.value?.layers ?? [])
  const isMultiLayer = computed(() => availableLayers.value.length > 0)

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

  function toggleLayer(layerId: string, visible: boolean) {
    const next = new Set(visibleLayerIds.value)
    if (visible) {
      next.add(layerId)
    }
    else {
      next.delete(layerId)
    }
    visibleLayerIds.value = next
  }

  watch(
    () => activeView.value,
    (view) => {
      if (view?.layers?.length) {
        const defaults = view.layers.filter(l =>
          l.id === 'front' || l.id === 'back' || l.id === 'pcb-top' || l.id === 'pcb-bottom',
        ).map(l => l.id)

        if (defaults.length === 0 && view.layers.length > 0) {
          defaults.push(view.layers[0].id)
        }
        visibleLayerIds.value = new Set(defaults)
      }
      else {
        visibleLayerIds.value = new Set()
      }
    },
    { immediate: true },
  )

  return {
    availableLayers,
    isMultiLayer,
    visibleLayerIds,
    firstVisibleLayerId,
    bottomVisibleLayerId,
    toggleLayer,
  }
}
