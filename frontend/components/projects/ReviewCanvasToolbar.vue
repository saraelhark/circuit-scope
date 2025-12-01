<script setup lang="ts">
import type { ViewerView } from "~/types/viewer"
import { Button } from "~/components/ui/button"

type Tool = "pan" | "circle"

interface Props {
    views: ViewerView[]
    currentViewId: string
    selectedTool: Tool
}

const props = defineProps<Props>()

const emit = defineEmits<{
    (e: "select-view", viewId: string): void
    (e: "select-tool", tool: Tool): void
    (e: "zoom-in" | "zoom-out" | "reset-zoom" | "flip-view"): void
}>()

const toolOptions: { label: string; value: Tool }[] = [
    { label: "Pan", value: "pan" },
    { label: "Circle", value: "circle" },
]

const activeClass = 'bg-cs-dark-green border-cs-dark-green text-white'
const inactiveClass = 'bg-cs-lighter-green text-cs-charcoal border-cs-whiteish hover:bg-cs-light-green hover:text-white'

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
        class="absolute left-3 top-3 z-20 flex gap-2 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur max-w-[calc(100vw-24px)] overflow-x-auto scrollbar-hide lg:max-w-none">
        <Button v-for="view in props.views" :key="view.id" type="button" variant="regular" size="sm"
            class="shrink-0 px-3 text-xs" :class="getButtonClass(props.currentViewId === view.id)"
            @click="emit('select-view', view.id)">
            {{ view.label }}
        </Button>
    </div>
    <div
        class="absolute left-1/2 bottom-6 -translate-x-1/2 z-20 flex items-center gap-3 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur lg:top-3 lg:bottom-auto">
        <div class="flex items-center gap-1">
            <Button v-for="tool in toolOptions" :key="tool.value" type="button" variant="regular" size="sm"
                class="px-3 text-xs" :class="getButtonClass(props.selectedTool === tool.value)"
                @click="emit('select-tool', tool.value)">
                {{ tool.label }}
            </Button>
        </div>
        <div class="h-4 w-px bg-border mx-1"></div>
        <div class="flex items-center gap-1">
            <Button v-if="props.currentViewId === 'pcb-3d'" variant="regular" size="sm" class="h-8 px-3 text-xs"
                @click="emit('flip-view')">
                Flip view
            </Button>
            <Button v-for="control in zoomControls" :key="control.action" variant="regular" size="sm"
                :class="control.class" @click="emit(control.action)">
                <span class="leading-none">{{ control.label }}</span>
            </Button>
        </div>
    </div>
</template>
