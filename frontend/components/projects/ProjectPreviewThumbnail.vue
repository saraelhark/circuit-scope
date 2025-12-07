<script setup lang="ts">
import { computed } from "vue"

import type { PreviewAsset, ProjectPreviewResponse } from "~/types/api/projects"
import { useProject } from "~/composables/useProjects"

const props = defineProps<{
  projectId: string
  thumbnailKind?: string | null
  sourceType?: string | null
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
  const photos = previews.photos ?? []

  const thumbnailKind = props.thumbnailKind ?? null
  const sourceType = props.sourceType ?? "kicad"

  if (sourceType === "images" || thumbnailKind === "photo") {
    return photos[0] ?? null
  }

  if (thumbnailKind === "schematic") {
    if (schematics[0]) return schematics[0]
  }

  if (thumbnailKind === "3d") {
    const renderPhoto =
      photos.find((photo) => photo.id === "board-3d-render") ?? photos[0] ?? null

    if (renderPhoto) {
      return renderPhoto
    }
  }

  const topLayout =
    layouts.find((layout) => /top|front/i.test(layout.title ?? layout.id ?? layout.filename)) ?? layouts[0]

  if (topLayout) {
    return topLayout
  }

  return schematics[0] ?? photos[0] ?? null
})

const thumbnailBackgroundClass = computed(() => {
  const previews = data.value
  const asset = selectedAsset.value
  if (!asset || !previews) return "bg-cs-black"

  const schematics = previews.schematics ?? []
  if (schematics.some((s) => s.id === asset.id)) {
    return "bg-cs-whiteish"
  }

  return "bg-cs-black"
})

const previewUrl = computed(() => selectedAsset.value?.url ?? null)
const previewAlt = computed(
  () => selectedAsset.value?.title ?? selectedAsset.value?.filename ?? "Project preview",
)

const isLoading = computed(() => status.value === "pending" || status.value === "idle")
</script>

<template>
  <div class="relative aspect-square w-full overflow-hidden rounded-md" :class="thumbnailBackgroundClass">
    <div v-if="isLoading" class="h-full w-full animate-pulse bg-white/10" />

    <img v-else-if="previewUrl" :src="previewUrl" :alt="previewAlt" class="h-full w-full object-contain" loading="lazy">

    <div v-else
      class="flex h-full items-center justify-center text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
      No preview
    </div>
  </div>
</template>
