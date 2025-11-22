<script setup lang="ts">
import { computed } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Textarea } from "~/components/ui/textarea"
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

const canResolveThreads = computed(() => props.canResolveThreads === true)

const emit = defineEmits<{
    (e: "update:newThreadContent", value: string): void
    (e: "update:replyContent", value: string): void
    (e: "open-thread", thread: CommentThread): void
    (e: "submit-new-thread"): void
    (e: "cancel-pending-pin"): void
    (e: "submit-reply"): void
    (e: "toggle-thread-resolution", thread: CommentThread): void
}>()

const localNewThreadContent = computed({
    get: () => props.newThreadContent,
    set: (value: string) => emit("update:newThreadContent", value),
})

const localReplyContent = computed({
    get: () => props.replyContent,
    set: (value: string) => emit("update:replyContent", value),
})

function threadLabel(threadId: string): number | string {
    const index = props.threads.findIndex((t) => t.id === threadId)
    return index >= 0 ? index + 1 : "?"
}
</script>

<template>
    <div class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">New comment</h3>
            <Button v-if="pendingPinPresent" size="sm" variant="ghost" class="text-muted-foreground"
                @click="$emit('cancel-pending-pin')">
                Cancel
            </Button>
        </div>
        <div v-if="formError"
            class="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {{ formError }}
        </div>
        <p v-if="!pendingPinPresent" class="text-sm text-muted-foreground">
            Draw a circle on the canvas to start a new thread.
        </p>
        <form v-if="pendingPinPresent" class="space-y-3 overflow-y-auto" @submit.prevent="$emit('submit-new-thread')">
            <div class="grid gap-2 p-2 text-sm">
                <label class="flex flex-col gap-1">
                    <span class="font-medium">Comment</span>
                    <Textarea v-model="localNewThreadContent" rows="3" placeholder="Share your feedback…" />
                </label>
            </div>
            <div class="flex justify-end gap-2">
                <Button type="submit" size="sm">Create thread</Button>
            </div>
        </form>
    </div>

    <div class="mt-4 flex-1 overflow-y-auto rounded-lg border p-4">
        <div class="mb-3 flex items-center justify-between text-sm text-muted-foreground">
            <span>
                {{ threads.length }} thread{{ threads.length === 1 ? '' : 's' }} total
            </span>
            <span v-if="threadStatus === 'pending'">Refreshing…</span>
        </div>
        <div v-if="threads.length === 0" class="text-sm text-muted-foreground">
            No comments yet. Draw a shape to start the first thread.
        </div>
        <div v-else class="space-y-3">
            <div v-for="thread in threads" :key="thread.id" class="rounded-md border p-3 text-sm" :class="{
                'border-primary bg-primary/5': thread.id === activeThreadId,
                'opacity-60': thread.is_resolved,
            }">
                <button type="button" class="flex w-full items-center justify-between text-left"
                    @click="$emit('open-thread', thread)">
                    <div>
                        <p class="font-medium">
                            Annotation #{{ threadLabel(thread.id) }} · {{ thread.view_id }}
                        </p>
                        <p class="text-xs text-muted-foreground">
                            {{ thread.comment_count }} comment{{ thread.comment_count === 1 ? '' : 's' }}
                        </p>
                    </div>
                    <Badge v-if="thread.is_resolved" variant="secondary">Resolved</Badge>
                </button>
                <div v-if="thread.id === activeThreadId" class="mt-3 space-y-3 border-t pt-3">
                    <div v-for="comment in thread.comments" :key="comment.id" class="space-y-1">
                        <p class="text-xs font-semibold">
                            {{ comment.author?.display_name ?? comment.guest_name ?? 'Guest' }}
                            <span class="ml-2 text-[11px] text-muted-foreground">
                                {{ formatDateTime(comment.created_at) }}
                            </span>
                        </p>
                        <p class="text-sm leading-relaxed">{{ comment.content }}</p>
                    </div>
                    <div v-if="canResolveThreads" class="flex flex-wrap items-center gap-2">
                        <Button size="sm" variant="outline" @click="$emit('toggle-thread-resolution', thread)">
                            {{ thread.is_resolved ? 'Reopen' : 'Mark-as-resolved' }}
                        </Button>
                    </div>
                    <div v-if="replyError"
                        class="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
                        {{ replyError }}
                    </div>
                    <form class="space-y-2 pt-1" @submit.prevent="$emit('submit-reply')">
                        <div class="grid gap-2 text-xs">
                            <label class="flex flex-col gap-1">
                                <span class="font-medium">Reply</span>
                                <Textarea v-model="localReplyContent" rows="3" placeholder="Write a reply…" />
                            </label>
                        </div>
                        <div class="flex justify-end">
                            <Button size="sm" type="submit">Post reply</Button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>
