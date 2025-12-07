<script setup lang="ts">
import { formatDateTime } from "~/lib/formatters"
import type { CommentThread } from "~/types/api/commentThreads"

interface Props {
    threads: CommentThread[]
    activeThreadId: string | null
    threadStatus: string | undefined
    pendingPinPresent: boolean
    formError: string | null
    replyError: string | null
    newThreadContent: string
    replyContent: string
    canResolveThreads?: boolean
}

const props = defineProps<Props>()


const emit = defineEmits<{
    (e: "update:newThreadContent", value: string): void
    (e: "update:replyContent", value: string): void
    (e: "open-thread", thread: CommentThread): void
    (e: "submit-new-thread"): void
    (e: "cancel-pending-pin"): void
    (e: "submit-reply"): void
    (e: "toggle-thread-resolution", thread: CommentThread): void
    (e: "highlight-thread", threadId: string): void
    (e: "unhighlight-thread"): void
}>()


function threadLabel(threadId: string): number | string {
    const index = props.threads.findIndex((t) => t.id === threadId)
    return index >= 0 ? index + 1 : "?"
}
</script>

<template>
    <div class="flex flex-col h-full">
        <div class="flex items-center justify-between p-4 pb-2">
            <h3 class="font-semibold text-lg">Comments</h3>
        </div>

        <div class="flex-1 overflow-y-auto px-4 pb-4 space-y-3">
            <div v-if="threads.length === 0" class="text-sm text-muted-foreground p-2">
                No comments yet. Click on the canvas to place a pin.
            </div>

            <div v-for="thread in threads" :key="thread.id"
                class="rounded-xl border p-4 text-sm transition-colors cursor-pointer group"
                :class="thread.id === activeThreadId ? 'bg-blue-50 border-blue-200' : 'bg-white hover:border-gray-300'"
                @click="$emit('open-thread', thread)" @mouseenter="$emit('highlight-thread', thread.id)"
                @mouseleave="$emit('unhighlight-thread')">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <div
                            class="h-6 w-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600">
                            {{ (thread.comments[0]?.author?.display_name || thread.comments[0]?.guest_name ||
                                'Guest').charAt(0).toUpperCase() }}
                        </div>

                        <div class="flex flex-col">
                            <div class="flex items-center gap-2 text-xs text-gray-500">
                                <span class="font-medium text-gray-900">#{{ threadLabel(thread.id) }}</span>
                                <span>·</span>
                                <span>{{ thread.view_id }}</span>
                            </div>
                            <div class="flex items-center gap-3 text-xs">
                                <span class="font-semibold text-gray-900">
                                    {{ thread.comments[0]?.author?.display_name || thread.comments[0]?.guest_name ||
                                        'Guest' }}
                                </span>
                                <span class="text-gray-400">
                                    {{ formatDateTime(thread.comments[0]?.created_at) }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div v-if="thread.is_resolved">
                        <svg class="text-green-600" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>
                </div>

                <p class="text-gray-800 text-sm leading-relaxed mb-2 pl-8">
                    {{ thread.comments[0]?.content }}
                </p>

                <div v-if="thread.comment_count > 1" class="pl-8">
                    <span class="text-xs font-medium text-blue-600 hover:underline">
                        {{ thread.comment_count - 1 }} repl{{ thread.comment_count - 1 === 1 ? 'y' : 'ies' }}
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>
