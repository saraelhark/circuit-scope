<script setup lang="ts">
import { computed } from "vue"
import { Share2 } from "lucide-vue-next"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import ProjectAssetViewer from "~/components/projects/ProjectAssetViewer.vue"
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

const projectStatusLabel = computed(() => {
  const status = project.value?.status
  return status && status.toLowerCase() === "closed" ? "Closed" : "Open"
})

const projectStatusVariant = computed(() =>
  projectStatusLabel.value === "Closed" ? "secondary" : "success",
)

const { data: previewData, status: previewStatus } = useAsyncData<ProjectPreviewResponse>(
  `project-${projectId.value}-previews`,
  () => getProjectPreviews(projectId.value),
  {
    watch: [projectId],
  },
)

const previews = computed(() => previewData.value)

const schematics = computed(() => previews.value?.schematics ?? [])
const layouts = computed(() => previews.value?.layouts ?? [])
const models = computed(() => previews.value?.models ?? [])
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
  <div v-else class="container py-4 max-w-5xl mx-auto">
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
      <div v-if="status === 'pending'" class="flex h-64 items-center justify-center text-muted-foreground">
        Loading project…
      </div>

      <div v-else-if="!project"
        class="rounded-lg border border-dashed border-muted-foreground/30 p-12 text-center text-muted-foreground">
        Project not found.
      </div>

      <div v-else class="flex flex-col gap-10">

        <div class="flex flex-col gap-4 border-b pb-4">
          <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div class="space-y-4 flex-1">
              <h1 class="text-3xl font-bold tracking-tight lg:text-3xl">{{ project.name }}</h1>
              <div class="flex items-center gap-3">
                <Badge :variant="projectStatusVariant" class="text-sm px-2 py-0.5">
                  {{ projectStatusLabel }}
                </Badge>
              </div>
            </div>

            <div class="flex flex-col gap-3 sm:flex-row shrink-0">
              <Button size="lg" class="text-base px-8 shadow-sm" @click="goToReview">
                Start Review
              </Button>
              <Button variant="outline" size="lg" class="text-base px-8 shadow-sm" @click="shareProject">
                <Share2 class="mr-2 h-4 w-4" />
                Share
              </Button>
            </div>
          </div>

          <div class="prose prose-lg text-muted-foreground max-w-none">
            <p v-if="project.description">{{ project.description }}</p>
            <p v-else class="italic opacity-50">No description provided.</p>
          </div>
        </div>

        <div>
          <h2 class="text-xl font-semibold tracking-tight mb-4">Previews</h2>

          <div v-if="previewStatus === 'pending'"
            class="flex h-64 items-center justify-center text-muted-foreground bg-muted/10">
            Generating previews…
          </div>
          <div v-else class="bg-card overflow-hidden">
            <div class="p-1">
              <ProjectAssetViewer :views="viewerViews" :initial-view-id="schematics.length ? 'schematic' : 'pcb-top'"
                :show-controls="true" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
