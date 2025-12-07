<script setup lang="ts">
import CommentPin from "~/components/projects/CommentPin.vue"
import CanvasCommentInput from "~/components/projects/CanvasCommentInput.vue"
import CanvasThreadPopover from "~/components/projects/CanvasThreadPopover.vue"
import type { ViewerAnnotation } from "~/components/projects/ReviewCanvas.vue"
import type { CommentThread } from "~/types/api/commentThreads"

defineProps<{
    pins: ViewerAnnotation[]
    activeThreadId?: string | null
    zoom: number
    pendingPin?: { x: number; y: number } | null
    activeThread?: CommentThread | null
    currentUserInitial?: string
    canResolveThreads?: boolean
    authorColorMap?: Map<string, string>
    currentUserColor?: string
}>()

const emit = defineEmits<{
    (e: "pinHover", id: string): void
    (e: "pinLeave", id: string): void
    (e: "pinClick", id: string): void
    (e: "submitComment", content: string): void
    (e: "cancelComment"): void
    (e: "reply", content: string): void
    (e: "resolveThread", thread: CommentThread): void
    (e: "closeThread"): void
}>()
</script>

<template>
    <div class="absolute inset-0 pointer-events-none" :style="{ zIndex: 100 }">
        <template v-for="pin in pins" :key="pin.id">
            <div v-if="activeThread?.id !== pin.id" class="absolute pointer-events-auto" :style="{
                left: `${pin.pinX * 100}%`,
                top: `${pin.pinY * 100}%`,
                transform: `translate(0, -100%) scale(${1 / zoom})`,
                transformOrigin: 'bottom left'
            }" @pointerdown.stop>
                <CommentPin :label="pin.data.initial" :comment="pin.data.comment" :author-name="pin.data.authorName"
                    :color="pin.data.color" :is-expanded="false" @mouseenter="emit('pinHover', pin.id)"
                    @mouseleave="emit('pinLeave', pin.id)" @click.stop="emit('pinClick', pin.id)" />
            </div>
        </template>

        <CanvasCommentInput v-if="pendingPin" :x="pendingPin.x" :y="pendingPin.y" :zoom="zoom"
            :initial="currentUserInitial" class="pointer-events-auto" @pointerdown.stop
            @submit="(content) => emit('submitComment', content)" @cancel="emit('cancelComment')" />

        <CanvasThreadPopover v-if="activeThread" :thread="activeThread" :x="activeThread.pin_x" :y="activeThread.pin_y"
            :zoom="zoom" :current-user-initial="currentUserInitial" :can-resolve-threads="canResolveThreads"
            :author-color-map="authorColorMap" :pin-color="pins.find(p => p.id === activeThread?.id)?.data.color"
            class="pointer-events-auto" @pointerdown.stop @reply="(content) => emit('reply', content)"
            @resolve="emit('resolveThread', activeThread!)" @close="emit('closeThread')" />
    </div>
</template>
