<script setup lang="ts">
defineProps<{
  commentCount: number
  viewCount: number
  timeAgo?: string
}>()
</script>

<template>
  <div class="flex items-center gap-4 text-xs text-white/70 font-primary">
    <div
      class="flex items-center gap-1"
      title="Comments"
    >
      <i class="far fa-comment h-3.5 w-3.5" />
      <span>{{ commentCount }}</span>
    </div>
    <div
      class="flex items-center gap-1"
      title="Views"
    >
      <i class="far fa-eye h-3.5 w-3.5" />
      <span>{{ viewCount }}</span>
    </div>
    <span v-if="timeAgo">{{ timeAgo }}</span>
  </div>
</template>
