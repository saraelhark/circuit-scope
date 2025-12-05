<script setup lang="ts">
import { computed } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import ProjectAssetViewer from "~/components/projects/ProjectAssetViewer.vue"
import ProjectImageCarousel from "~/components/projects/ProjectImageCarousel.vue"
import { buildViewerViews } from "~/lib/reviewViewer"
import type { Project, ProjectPreviewResponse } from "~/types/api/projects"
import { useProject } from "~/composables/useProjects"

definePageMeta({
  layout: "default",
})

const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.id as string)

const { getProject, getProjectPreviews } = useProject()

const { data, error, refresh, status } = useAsyncData<Project>(
  `project-${projectId.value}`,
  () => getProject(projectId.value),
  {
    watch: [projectId],
  },
)

const project = computed(() => data.value)

let pollInterval: NodeJS.Timeout | null = null

watch(project, (newVal) => {
  if (newVal?.processing_status === "queued" || newVal?.processing_status === "processing") {
    if (!pollInterval) {
      pollInterval = setInterval(() => {
        refresh()
      }, 2000)
    }
  } else {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
      refreshPreviews()
    }
  }
}, { immediate: true })

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

const projectStatusLabel = computed(() => {
  const status = project.value?.status
  return status && status.toLowerCase() === "closed" ? "Closed" : "Open"
})

const projectStatusVariant = computed(() =>
  projectStatusLabel.value === "Closed" ? "secondary" : "success",
)

const { data: previewData, status: previewStatus, refresh: refreshPreviews } = useAsyncData<ProjectPreviewResponse>(
  `project-${projectId.value}-previews`,
  () => getProjectPreviews(projectId.value),
  {
    watch: [projectId],
    immediate: false,
  },
)

onMounted(() => {
  if (project.value?.processing_status === 'completed') {
    refreshPreviews()
  }
})

watch(project, (p) => {
  if (p?.processing_status === 'completed' && !previewData.value) {
    refreshPreviews()
  }
})

const previews = computed(() => previewData.value)

const schematics = computed(() => previews.value?.schematics ?? [])
const layouts = computed(() => previews.value?.layouts ?? [])
const models = computed(() => previews.value?.models ?? [])
const photos = computed(() => previews.value?.photos ?? [])
const viewerViews = computed(() => buildViewerViews(schematics.value, layouts.value, models.value))

useHead(() => ({
  title: project.value ? `${project.value.name} – Project – Circuit Scope` : "Project – Circuit Scope",
}))

function goToReview() {
  router.push(`/projects/${projectId.value}/review`)
}

async function shareProject() {
  if (!import.meta.client) return

  try {
    const origin = window.location.origin
    const url = `${origin}/projects/${projectId.value}`

    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(url)
    } else {
      console.warn("Clipboard API not available. Could not copy project link automatically.", url)
    }
  } catch (error) {
    console.error("Failed to copy project link", error)
  }
}
</script>

<template>
  <NuxtPage v-if="$route.name === 'projects-id-review'" />
  <div v-else
    class="min-h-[calc(100vh-3.5rem)] container px-4 sm:px-8 py-8 max-w-6xl mx-auto bg-cs-light-green border-x-4 border-y-0 border-white">
    <div v-if="error">
      <div class="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-destructive">
        <h3 class="font-semibold">Failed to load project</h3>
        <p class="mt-1 text-sm">{{ error?.message ?? "Please try again later." }}</p>
        <Button variant="outline" class="mt-4 border-destructive/50 hover:bg-destructive/20" @click="refresh">
          Retry
        </Button>
      </div>
    </div>

    <div v-else>
      <div v-if="status === 'pending' && !project" class="flex h-64 items-center justify-center text-cs-whiteish">
        Loading project…
      </div>

      <div v-else-if="!project"
        class="rounded-lg border border-dashed border-cs-whiteish/30 p-12 text-center text-cs-whiteish">
        Project not found.
      </div>

      <div v-else class="flex flex-col gap-4 sm:gap-6">

        <div v-if="project.processing_status === 'queued' || project.processing_status === 'processing'"
          class="rounded-lg border border-blue-200 bg-blue-50 p-4 text-blue-800 dark:border-blue-900 dark:bg-blue-950/30 dark:text-blue-200">
          <div class="flex items-center gap-3">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent"></div>
            <p class="font-medium">Processing project assets...</p>
          </div>
          <p class="mt-1 text-sm ml-7 opacity-90">
            This may take a few moments. The page will update automatically.
          </p>
        </div>

        <div v-else-if="project.processing_status === 'failed'"
          class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
          <h3 class="font-semibold flex items-center gap-2">
            <span>Processing Failed</span>
          </h3>
          <p class="mt-1 text-sm">{{ project.processing_error || "An unknown processing error occurred." }}</p>
        </div>

        <div class="flex flex-col gap-4 border-b pb-4">
          <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div class="space-y-2 flex-1">
              <div class="flex items-center justify-between gap-2">
                <h1 class="text-2xl font-bold tracking-tight lg:text-3xl truncate">{{ project.name }}</h1>
              </div>
              <div class="flex items-center justify-between md:justify-start gap-3">
                <Badge :variant="projectStatusVariant" class="text-sm px-2 py-0.5">
                  {{ projectStatusLabel }}
                </Badge>

                <div class="flex items-center gap-2 md:hidden">
                  <Button variant="regular" size="icon" class="h-9 w-9" @click="shareProject">
                    <i class="fas fa-share-alt h-4 w-4"></i>
                  </Button>
                  <Button size="sm" variant="regular" class="h-9 px-4" @click="goToReview">
                    Review
                  </Button>
                </div>
              </div>
            </div>

            <div class="hidden md:flex flex-col gap-3 sm:flex-row shrink-0">
              <Button variant="regular" @click="shareProject">
                <i class="fas fa-share-alt h-4 w-4"></i>
              </Button>
              <Button variant="cta" @click="goToReview">
                Go to Review
              </Button>
            </div>
          </div>

          <div class="prose prose-sm text-cs-whiteish max-w-none" v-if="project.description">
            <p>{{ project.description }}</p>
          </div>

          <div v-if="project.tags && project.tags.length" class="mt-2 flex flex-wrap gap-1 font-secondary">
            <Badge v-for="tag in project.tags" :key="tag" variant="outline"
              class="border-cs-gold bg-cs-blue/80 text-cs-whiteish text-[11px] px-2 py-0.5 uppercase tracking-wide rounded-sm">
              {{ tag }}
            </Badge>
          </div>
        </div>

        <div>
          <h2 class="text-xl font-semibold tracking-tight mb-4">Previews</h2>

          <div v-if="previewStatus === 'pending'"
            class="flex h-64 items-center justify-center text-cs-whiteish bg-muted/10">
            Generating previews…
          </div>
          <div v-else class="overflow-hidden">
            <ProjectImageCarousel v-if="project.source_type === 'images'" :photos="photos" />
            <ProjectAssetViewer v-else :views="viewerViews"
              :initial-view-id="schematics.length ? 'schematic' : 'pcb-top'" :show-controls="true" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
