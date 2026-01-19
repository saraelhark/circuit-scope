<script setup lang="ts">
import { useTimeAgo } from '@vueuse/core'
import type { Project } from '~/types/api/projects'
import ProjectPreviewThumbnail from '~/components/projects/ProjectPreviewThumbnail.vue'
import ProjectStats from '~/components/projects/ProjectStats.vue'
import { Badge } from '~/components/ui/badge'

const props = defineProps<{
  project: Project
}>()

const timeAgo = useTimeAgo(() => new Date(props.project.created_at))

const MAX_DESCRIPTION_LENGTH = 80

function formattedDescription(description: string | null) {
  const desc = description?.trim()
  if (!desc) return ''
  if (desc.length <= MAX_DESCRIPTION_LENGTH) {
    return desc
  }
  return `${desc.slice(0, MAX_DESCRIPTION_LENGTH).trimEnd()}…`
}
</script>

<template>
  <NuxtLink
    :to="`/projects/${project.id}`"
    class="group flex flex-col rounded-lg border border-cs-border bg-cs-card overflow-hidden transition-all hover:border-cs-brand text-white shadow-sm"
  >
    <div class="aspect-[4/3] w-full overflow-hidden bg-cs-panel flex items-center justify-center">
      <ProjectPreviewThumbnail
        :project-id="project.id"
        :thumbnail-kind="project.thumbnail_kind"
        :source-type="project.source_type"
        class="w-full h-full object-cover"
      />
    </div>

    <div class="flex flex-col gap-2 p-4">
      <h3
        class="text-base font-bold leading-tight tracking-tight text-white font-primary group-hover:underline line-clamp-1"
      >
        {{ project.name }}
      </h3>

      <p
        v-if="project.description"
        class="text-sm text-white/70 line-clamp-2 font-secondary min-h-[2.5rem]"
      >
        {{ formattedDescription(project.description) }}
      </p>

      <div
        v-if="project.tags && project.tags.length"
        class="flex flex-wrap gap-1 font-secondary"
      >
        <Badge
          v-for="tag in project.tags.slice(0, 3)"
          :key="tag"
          variant="outline"
          class="border-cs-copper bg-cs-panel text-cs-copper text-[10px] px-1.5 py-0 uppercase tracking-wide rounded-sm"
        >
          {{ tag }}
        </Badge>
        <span
          v-if="project.tags.length > 3"
          class="text-[10px] text-white/50"
        >
          +{{ project.tags.length - 3 }}
        </span>
      </div>

      <div class="mt-auto pt-2 border-t border-cs-border/50">
        <ProjectStats
          :comment-count="project.total_comment_count"
          :view-count="project.view_count"
          :time-ago="timeAgo"
        />
      </div>
    </div>
  </NuxtLink>
</template>
