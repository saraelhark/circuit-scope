<script setup lang="ts">
import { computed } from "vue"

import type { PreviewAsset, ProjectPreviewResponse } from "~/types/api/projects"
import { useProject } from "~/composables/useProjects"

const props = defineProps<{
  projectId: string
}>()

const projectId = computed(() => props.projectId)

const { getProjectPreviews } = useProject()

const { data, status } = useAsyncData<ProjectPreviewResponse>(
  `project-${projectId.value}-previews-thumbnail`,
  () => getProjectPreviews(projectId.value),
  {
    server: false,
    watch: [projectId],
  },
)

const selectedAsset = computed<PreviewAsset | null>(() => {
  const previews = data.value
  if (!previews) {
    return null
  }

  const layouts = previews.layouts ?? []
  const schematics = previews.schematics ?? []

  const topLayout =
    layouts.find((layout) => /top|front/i.test(layout.title ?? layout.id ?? layout.filename)) ?? layouts[0]

  if (topLayout) {
    return topLayout
  }

  return schematics[0] ?? null
})

const previewUrl = computed(() => selectedAsset.value?.url ?? null)
const previewAlt = computed(
  () => selectedAsset.value?.title ?? selectedAsset.value?.filename ?? "Project preview",
)

const isLoading = computed(() => status.value === "pending" || status.value === "idle")
</script>

<template>
  <div class="relative aspect-square w-full overflow-hidden rounded-md border bg-[#001124]">
    <div v-if="isLoading" class="h-full w-full animate-pulse bg-white/10" />

    <img v-else-if="previewUrl" :src="previewUrl" :alt="previewAlt" class="h-full w-full object-contain" loading="lazy">

    <div v-else
      class="flex h-full items-center justify-center text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
      No preview
    </div>
  </div>
</template>
