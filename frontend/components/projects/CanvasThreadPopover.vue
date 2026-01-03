<script setup lang="ts">
import { ref, computed } from 'vue'
import { formatDateTime } from '~/lib/formatters'
import type { CommentThread } from '~/types/api/commentThreads'
import CommentIcon from '~/components/projects/CommentIcon.vue'

interface Props {
  thread: CommentThread
  x: number
  y: number
  zoom?: number
  currentUserInitial?: string
  canResolveThreads?: boolean
  authorColorMap?: Map<string, string>
  pinColor?: string
  currentUserColor?: string
}

const props = withDefaults(defineProps<Props>(), {
  zoom: 1,
  currentUserInitial: 'G',
  canResolveThreads: false,
  pinColor: '#FFD02B',
  currentUserColor: '#FFD02B',
})

const emit = defineEmits<{
  (e: 'reply', content: string): void
  (e: 'close'): void
  (e: 'resolve'): void
}>()

const replyContent = ref('')

function handleReply() {
  if (!replyContent.value.trim()) return
  emit('reply', replyContent.value)
  replyContent.value = ''
}

const pinInitial = computed(() => {
  const first = props.thread.comments[0]
  const name = first?.author?.display_name || first?.guest_name || 'Guest'
  return name.charAt(0).toUpperCase()
})

function getCommentColor(comment: CommentThread['comments'][0]) {
  if (!props.authorColorMap) return '#FFD02B'
  const key = comment.author_id || comment.guest_name || 'Anonymous'
  return props.authorColorMap.get(key) || '#FFD02B'
}
</script>

<template>
  <div
    class="absolute z-[100] flex items-end gap-2"
    :style="{
      left: `${x * 100}%`,
      top: `${y * 100}%`,
      transform: `translate(0, -100%) scale(${1 / zoom})`,
      transformOrigin: 'bottom left',
    }"
    @click.stop
    @mousedown.stop
  >
    <div class="relative flex flex-col items-center">
      <CommentIcon
        :initial="pinInitial"
        size="lg"
        :color="pinColor"
      />
    </div>

    <div
      class="w-[320px] max-w-[90vw] rounded-xl bg-white shadow-xl border border-gray-100 overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200"
    >
      <div class="flex items-center justify-between border-b p-3 bg-gray-50/50">
        <span class="font-semibold text-sm">Comment</span>
        <div class="flex items-center gap-2">
          <button
            v-if="!thread.is_resolved && canResolveThreads"
            class="h-6 w-6 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-500"
            title="Resolve"
            @click="$emit('resolve')"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </button>
          <button
            class="h-6 w-6 flex items-center justify-center rounded-full hover:bg-gray-200 text-gray-500"
            @click="$emit('close')"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line
                x1="18"
                y1="6"
                x2="6"
                y2="18"
              />
              <line
                x1="6"
                y1="6"
                x2="18"
                y2="18"
              />
            </svg>
          </button>
        </div>
      </div>

      <div class="flex flex-col max-h-[300px] overflow-y-auto">
        <div
          v-for="(comment, index) in thread.comments"
          :key="comment.id"
          class="p-4"
          :class="{ 'border-t': index > 0 }"
        >
          <div class="flex items-center gap-2 mb-1">
            <div
              class="h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold text-cs-charcoal"
              :style="{ backgroundColor: getCommentColor(comment) }"
            >
              {{ (comment.author?.display_name || comment.guest_name
                || 'Guest').charAt(0).toUpperCase() }}
            </div>
            <span class="font-semibold text-sm">{{ comment.author?.display_name || comment.guest_name
              || 'Guest' }}</span>
            <span class="text-xs text-muted-foreground ml-auto">{{ formatDateTime(comment.created_at)
            }}</span>
          </div>
          <p class="text-sm text-gray-700 pl-8 leading-relaxed">
            {{ comment.content }}
          </p>
        </div>
      </div>

      <div class="p-3 bg-gray-50 border-t">
        <div class="flex items-center gap-2">
          <div
            class="h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold text-cs-charcoal shrink-0"
            :style="{ backgroundColor: currentUserColor }"
          >
            {{ currentUserInitial }}
          </div>
          <div
            class="flex-1 flex items-center rounded-full bg-white px-3 py-1.5 border border-gray-200 focus-within:border-gray-400 focus-within:ring-1 focus-within:ring-gray-400 transition-all"
          >
            <input
              v-model="replyContent"
              type="text"
              placeholder="Reply"
              class="flex-1 bg-transparent outline-none text-sm text-gray-700 min-w-0"
              @keydown.enter.prevent="handleReply"
            >
            <button
              class="ml-2 h-6 w-6 flex items-center justify-center rounded-full transition-colors shrink-0"
              :class="replyContent.trim() ? 'bg-cs-dark-green text-white hover:opacity-90' : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
              :disabled="!replyContent.trim()"
              @click="handleReply"
            >
              <svg
                width="10"
                height="10"
                viewBox="0 0 12 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M6 0L4.9425 1.0575L9.1275 5.25H0V6.75H9.1275L4.9425 10.9425L6 12L12 6L6 0Z"
                  fill="currentColor"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
