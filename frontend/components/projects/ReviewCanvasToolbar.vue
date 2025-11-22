<script setup lang="ts">
import type { ViewerView } from "~/types/viewer"

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
    (e: "zoom-in"): void
    (e: "zoom-out"): void
    (e: "reset-zoom"): void
    (e: "flip-view"): void
}>()

const toolOptions: { label: string; value: Tool }[] = [
    { label: "Pan", value: "pan" },
    { label: "Circle", value: "circle" },
]
</script>

<template>
    <div class="absolute left-3 top-3 z-20 flex gap-2 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur">
        <button v-for="view in props.views" :key="view.id" type="button"
            class="rounded-md border px-3 py-1 text-xs font-medium" :class="props.currentViewId === view.id
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-border bg-background hover:border-primary/60'
                " @click="emit('select-view', view.id)">
            {{ view.label }}
        </button>
    </div>
    <div
        class="absolute left-1/2 top-3 z-20 flex -translate-x-1/2 items-center gap-3 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur">
        <div class="flex items-center gap-1">
            <button v-for="tool in toolOptions" :key="tool.value" type="button"
                class="rounded-md px-2 py-1 text-xs font-medium" :class="props.selectedTool === tool.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-background hover:bg-muted'
                    " @click="emit('select-tool', tool.value)">
                {{ tool.label }}
            </button>
        </div>
        <div class="flex items-center gap-1">
            <button v-if="props.currentViewId === 'pcb-3d'" class="rounded-md border px-2 py-1 text-xs"
                @click="emit('flip-view')">Flip View</button>
            <button class="rounded-md border px-2 py-1 text-xs" @click="emit('zoom-out')">-</button>
            <button class="rounded-md border px-2 py-1 text-xs" @click="emit('zoom-in')">+</button>
            <button class="rounded-md border px-2 py-1 text-xs" @click="emit('reset-zoom')">Reset</button>
        </div>
    </div>
</template>
