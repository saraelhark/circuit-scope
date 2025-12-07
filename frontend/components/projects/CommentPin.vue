<script setup lang="ts">
import CommentIcon from "~/components/projects/CommentIcon.vue"

interface Props {
  label: string
  isExpanded?: boolean
  comment?: string
  authorName?: string
  isDraft?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isExpanded: false,
  comment: "",
  authorName: "Guest",
  isDraft: false,
})

const emit = defineEmits<{
  (e: "mouseenter"): void
  (e: "mouseleave"): void
  (e: "click", event: MouseEvent): void
}>()
</script>

<template>
  <div class="absolute top-0 left-0 select-none" :style="{ zIndex: isExpanded ? 50 : 10 }">
    <div class="relative flex -translate-y-[100%] transform flex-col items-center"
      :class="{ 'cursor-grab': isDraft, 'cursor-pointer': !isDraft }" @mouseenter="$emit('mouseenter')"
      @mouseleave="$emit('mouseleave')" @click="(e) => $emit('click', e)">

      <!-- Icon Container -->
      <div class="relative flex items-center justify-center transition-transform duration-200"
        :class="{ 'scale-125': isExpanded, 'opacity-80': isDraft }">
        <CommentIcon :initial="label" size="lg" />
      </div>

      <div v-if="isExpanded && comment"
        class="absolute left-full top-1/2 ml-3 -translate-y-1/2 w-64 rounded-xl bg-white p-3 shadow-xl border border-gray-100 animate-in fade-in slide-in-from-left-2 duration-200">
        <div class="flex items-center gap-2 mb-1">
          <CommentIcon :initial="label" size="sm" />
          <span class="text-xs font-semibold text-gray-900 truncate">{{ authorName }}</span>
          <span class="text-[10px] text-gray-400 ml-auto">Just now</span>
        </div>
        <p class="text-sm text-gray-600 line-clamp-3 leading-relaxed">
          {{ comment }}
        </p>
      </div>
    </div>
  </div>
</template>
