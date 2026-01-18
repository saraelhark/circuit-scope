<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { formatDateTime } from '~/lib/formatters'
import type { CommentThread } from '~/types/api/commentThreads'

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
  canDeleteThreads?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:newThreadContent', value: string): void
  (e: 'update:replyContent', value: string): void
  (e: 'open-thread', thread: CommentThread): void
  (e: 'submit-new-thread'): void
  (e: 'cancel-pending-pin'): void
  (e: 'submit-reply', content: string): void
  (e: 'toggle-thread-resolution', thread: CommentThread): void
  (e: 'highlight-thread', threadId: string): void
  (e: 'unhighlight-thread'): void
  (e: 'delete-thread', threadId: string): void
  (e: 'thread-selected', threadId: string): void
  (e: 'thread-deselected'): void
}>()

const expandedThreadId = ref<string | null>(null)
const deleteModalThreadId = ref<string | null>(null)
const replyText = ref('')
const replyInputRef = ref<HTMLTextAreaElement | null>(null)

const threadToDelete = computed(() => {
  if (!deleteModalThreadId.value) return null
  return props.threads.find(t => t.id === deleteModalThreadId.value) || null
})

watch(() => props.activeThreadId, (newId) => {
  if (newId && newId !== expandedThreadId.value) {
    expandedThreadId.value = newId
  }
})

function threadLabel(threadId: string): number | string {
  const index = props.threads.findIndex(t => t.id === threadId)
  return index >= 0 ? index + 1 : '?'
}

function toggleThread(thread: CommentThread) {
  if (expandedThreadId.value === thread.id) {
    expandedThreadId.value = null
    emit('thread-deselected')
  }
  else {
    expandedThreadId.value = thread.id
    emit('thread-selected', thread.id)
    emit('open-thread', thread)
    nextTick(() => {
      replyInputRef.value?.focus()
    })
  }
}

function openDeleteModal(e: Event, threadId: string) {
  e.stopPropagation()
  deleteModalThreadId.value = threadId
}

function confirmDelete() {
  if (deleteModalThreadId.value) {
    emit('delete-thread', deleteModalThreadId.value)
    deleteModalThreadId.value = null
  }
}

function cancelDelete() {
  deleteModalThreadId.value = null
}

function submitReply(e: Event) {
  e.stopPropagation()
  if (replyText.value.trim()) {
    emit('submit-reply', replyText.value.trim())
    replyText.value = ''
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submitReply(e)
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="flex items-center justify-between p-4 pb-2">
      <h3 class="font-semibold text-lg">
        Comments
      </h3>
    </div>

    <div class="flex-1 overflow-y-auto px-4 pb-4 space-y-3">
      <div
        v-if="threads.length === 0"
        class="text-sm text-muted-foreground p-2"
      >
        No comments yet. Click on the canvas to place a pin.
      </div>

      <div
        v-for="thread in threads"
        :key="thread.id"
        class="rounded-xl border text-sm transition-colors group"
        :class="expandedThreadId === thread.id ? 'bg-blue-50 border-blue-200' : 'bg-white hover:border-gray-300'"
        @mouseenter="$emit('highlight-thread', thread.id)"
        @mouseleave="$emit('unhighlight-thread')"
      >
        <!-- Thread Header (clickable to expand/collapse) -->
        <div
          class="p-4 cursor-pointer"
          @click="toggleThread(thread)"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-2">
              <div class="flex items-center gap-1">
                <svg
                  class="transition-transform text-gray-400"
                  :class="expandedThreadId === thread.id ? 'rotate-90' : ''"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
                <div
                  class="h-6 w-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600"
                >
                  {{ (thread.comments[0]?.author?.display_name || thread.comments[0]?.guest_name
                    || 'Guest').charAt(0).toUpperCase() }}
                </div>
              </div>

              <div class="flex flex-col">
                <div class="flex items-center gap-2 text-xs text-gray-500">
                  <span class="font-medium text-gray-900">#{{ threadLabel(thread.id) }}</span>
                  <span>·</span>
                  <span>{{ thread.view_id }}</span>
                </div>
                <div class="flex items-center gap-3 text-xs">
                  <span class="font-semibold text-gray-900">
                    {{ thread.comments[0]?.author?.display_name || thread.comments[0]?.guest_name
                      || 'Guest' }}
                  </span>
                  <span class="text-gray-400">
                    {{ formatDateTime(thread.comments[0]?.created_at) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <div v-if="thread.is_resolved">
                <svg
                  class="text-green-600"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <button
                v-if="canDeleteThreads"
                class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-100 rounded text-gray-400 hover:text-red-600"
                title="Delete thread"
                @click="openDeleteModal($event, thread.id)"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          </div>

          <p class="text-gray-800 text-sm leading-relaxed pl-9">
            {{ thread.comments[0]?.content }}
          </p>

          <div
            v-if="thread.comment_count > 1 && expandedThreadId !== thread.id"
            class="pl-9 mt-1"
          >
            <span class="text-xs font-medium text-blue-600">
              {{ thread.comment_count - 1 }} repl{{ thread.comment_count - 1 === 1 ? 'y' : 'ies' }}
            </span>
          </div>
        </div>

        <!-- Expanded Replies Section -->
        <div
          v-if="expandedThreadId === thread.id && thread.comments.length > 1"
          class="border-t border-blue-200 bg-blue-50/50"
        >
          <div class="pl-9 pr-4 py-2 space-y-3">
            <div
              v-for="comment in thread.comments.slice(1)"
              :key="comment.id"
              class="flex gap-2"
            >
              <div
                class="h-5 w-5 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600 shrink-0 mt-0.5"
              >
                {{ (comment.author?.display_name || comment.guest_name || 'G').charAt(0).toUpperCase() }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 text-xs">
                  <span class="font-semibold text-gray-900">
                    {{ comment.author?.display_name || comment.guest_name || 'Guest' }}
                  </span>
                  <span class="text-gray-400">
                    {{ formatDateTime(comment.created_at) }}
                  </span>
                </div>
                <p class="text-gray-700 text-sm mt-0.5">
                  {{ comment.content }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Reply Input (shown when expanded) -->
        <div
          v-if="expandedThreadId === thread.id"
          class="border-t border-blue-200 p-3"
          @click.stop
        >
          <div class="flex gap-2">
            <textarea
              ref="replyInputRef"
              v-model="replyText"
              placeholder="Write a reply..."
              rows="1"
              class="flex-1 px-3 py-2 text-sm border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              @keydown="handleKeyDown($event)"
            />
            <button
              class="px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!replyText.trim()"
              @click="submitReply($event)"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="deleteModalThreadId"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50"
        @click.self="cancelDelete"
      >
        <div class="bg-white rounded-lg shadow-xl max-w-sm w-full mx-4 overflow-hidden">
          <div class="p-4 border-b">
            <h3 class="text-lg font-semibold text-gray-900">
              Delete Comment Thread
            </h3>
          </div>
          <div class="p-4">
            <p class="text-sm text-gray-600 mb-2">
              Are you sure you want to delete this comment thread?
            </p>
            <div
              v-if="threadToDelete"
              class="bg-gray-50 rounded-lg p-3 text-sm"
            >
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium text-gray-900">
                  #{{ threadLabel(threadToDelete.id) }}
                </span>
                <span class="text-gray-500">·</span>
                <span class="text-gray-500">{{ threadToDelete.view_id }}</span>
              </div>
              <p class="text-gray-700 line-clamp-2">
                {{ threadToDelete.comments[0]?.content }}
              </p>
              <p
                v-if="threadToDelete.comment_count > 1"
                class="text-xs text-gray-500 mt-1"
              >
                This will also delete {{ threadToDelete.comment_count - 1 }} repl{{ threadToDelete.comment_count - 1 === 1 ? 'y' : 'ies' }}.
              </p>
            </div>
            <p class="text-xs text-red-600 mt-3">
              This action cannot be undone.
            </p>
          </div>
          <div class="p-4 bg-gray-50 flex justify-end gap-2">
            <button
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              @click="cancelDelete"
            >
              Cancel
            </button>
            <button
              class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
              @click="confirmDelete"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
