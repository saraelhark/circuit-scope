<script setup lang="ts">
import { computed } from 'vue'
import type { ViewerView } from '~/types/viewer'
import { Button } from '~/components/ui/button'

type Tool = 'pan' | 'pin'

interface Props {
  views: ViewerView[]
  currentViewId: string
  selectedTool: Tool
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'select-view', viewId: string): void
  (e: 'select-tool', tool: Tool): void
  (e: 'zoom-in' | 'zoom-out' | 'reset-zoom' | 'flip-view'): void
}>()

const isPhotoMode = computed(
  () =>
    props.views.length > 0
    && props.views.every(view => view.id.startsWith('photo-')),
)

const currentIndex = computed(() => {
  if (!props.views.length) return 0
  const idx = props.views.findIndex(view => view.id === props.currentViewId)
  return idx === -1 ? 0 : idx
})

const totalViews = computed(() => props.views.length)

function goToOffset(offset: number) {
  if (!props.views.length) return
  const nextIndex = (currentIndex.value + offset + props.views.length) % props.views.length
  const nextView = props.views[nextIndex]
  if (nextView) {
    emit('select-view', nextView.id)
  }
}

const toolOptions: { label: string, value: Tool }[] = [
  { label: 'Pan', value: 'pan' },
  { label: 'Comment', value: 'pin' },
]

const activeClass = 'bg-cs-dark-green border-cs-dark-green text-white'
const inactiveClass = 'bg-cs-light-green text-cs-charcoal border-cs-whiteish hover:bg-cs-light-green hover:text-white'

function getButtonClass(isActive: boolean) {
  return isActive ? activeClass : inactiveClass
}

const zoomControls = [
  { label: '−', action: 'zoom-out' as const, class: 'h-8 w-8 p-0 text-xs' },
  { label: '+', action: 'zoom-in' as const, class: 'h-8 w-8 p-0 text-xs' },
  { label: 'Reset', action: 'reset-zoom' as const, class: 'h-8 px-3 text-xs' },
]
</script>

<template>
  <div
    class="absolute left-3 top-3 z-20 flex gap-2 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur max-w-[calc(100vw-24px)] overflow-x-auto scrollbar-hide lg:max-w-none"
  >
    <template v-if="isPhotoMode">
      <div class="flex items-center gap-2">
        <Button
          type="button"
          variant="regular"
          size="sm"
          class="h-8 w-8 p-0 text-xs"
          @click="goToOffset(-1)"
        >
          <span class="leading-none">&lt;</span>
        </Button>
        <span class="text-xs font-mono">
          {{ currentIndex + 1 }} / {{ totalViews }}
        </span>
        <Button
          type="button"
          variant="regular"
          size="sm"
          class="h-8 w-8 p-0 text-xs"
          @click="goToOffset(1)"
        >
          <span class="leading-none">&gt;</span>
        </Button>
      </div>
    </template>
    <template v-else>
      <Button
        v-for="view in props.views"
        :key="view.id"
        type="button"
        variant="regular"
        size="sm"
        class="shrink-0 px-3 text-xs"
        :class="getButtonClass(props.currentViewId === view.id)"
        @click="emit('select-view', view.id)"
      >
        {{ view.label }}
      </Button>
    </template>
  </div>
  <div
    class="absolute left-1/2 bottom-6 -translate-x-1/2 z-20 flex items-center gap-3 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur lg:top-3 lg:bottom-auto"
  >
    <div class="flex items-center gap-1">
      <Button
        v-for="tool in toolOptions"
        :key="tool.value"
        type="button"
        variant="regular"
        size="sm"
        class="px-3 text-xs"
        :class="getButtonClass(props.selectedTool === tool.value)"
        :title="tool.label"
        @click="emit('select-tool', tool.value)"
      >
        <i
          v-if="tool.value === 'pan'"
          class="fa-regular fa-hand-pointer text-lg"
        />
        <i
          v-else-if="tool.value === 'pin'"
          class="fa-regular fa-comment text-lg"
        />
        <span v-else>{{ tool.label }}</span>
      </Button>
    </div>
    <div class="h-4 w-px bg-border mx-1" />
    <div class="flex items-center gap-1">
      <Button
        v-if="props.currentViewId === 'pcb-3d'"
        variant="regular"
        size="sm"
        class="h-8 px-3 text-xs"
        @click="emit('flip-view')"
      >
        Flip view
      </Button>
      <Button
        v-for="control in zoomControls"
        :key="control.action"
        variant="regular"
        size="sm"
        :class="control.class"
        @click="emit(control.action)"
      >
        <span class="leading-none">{{ control.label }}</span>
      </Button>
    </div>
  </div>
</template>
