<script setup lang="ts">
import { computed } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { formatDateTime } from "~/lib/formatters"
import ProjectAssetViewer, { type ViewerView } from "~/components/projects/ProjectAssetViewer.vue"
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
const viewerViews = computed<ViewerView[]>(() => {
  const views: ViewerView[] = []

  if (schematics.value.length) {
    views.push({
      id: "schematic",
      label: "Schematic",
      asset: schematics.value[0],
      fallbackMessage: "No schematic SVG generated yet.",
    })
  } else {
    views.push({
      id: "schematic",
      label: "Schematic",
      asset: undefined,
      fallbackMessage: "No schematic previews available.",
    })
  }

  const topLayout = layouts.value.find((layout) => /top|front/i.test(layout.title ?? layout.id)) ?? layouts.value[0]
  const bottomLayout = layouts.value.find((layout) => /bottom|back/i.test(layout.title ?? layout.id))

  views.push({
    id: "pcb-top",
    label: "PCB Top",
    asset: topLayout ?? null,
    fallbackMessage: layouts.value.length
      ? "No top-side layout detected; showing first layout available."
      : "No PCB layout previews available.",
  })

  views.push({
    id: "pcb-bottom",
    label: "PCB Bottom",
    asset: bottomLayout ?? (layouts.value.length > 1 ? layouts.value[1] : null),
    fallbackMessage: layouts.value.length > 1
      ? "No bottom-side layout detected; showing alternative layout."
      : "No additional PCB layout previews available.",
  })

  return views
})

useHead(() => ({
  title: project.value ? `${project.value.name} – Project – Circuit Scope` : "Project – Circuit Scope",
}))

function goToReview() {
  router.push(`/projects/${projectId.value}/review`)
}
</script>

<template>
  <!-- Render nested routes such as /projects/:id/review -->
  <NuxtPage v-if="$route.name === 'projects-id-review'" />
  <!-- Show project details only on the main project route -->
  <div v-else class="space-y-6">
    <Card v-if="error">
      <CardHeader>
        <CardTitle class="text-xl">Failed to load project</CardTitle>
        <CardDescription>{{ error?.message ?? "Please try again later." }}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="secondary" @click="refresh">
          Retry
        </Button>
      </CardContent>
    </Card>

    <div v-else>
      <div v-if="status === 'pending'" class="flex h-32 items-center justify-center text-muted-foreground">
        Loading project…
      </div>

      <div v-else-if="!project"
        class="rounded-lg border border-dashed border-muted-foreground/30 p-6 text-center text-sm text-muted-foreground">
        Project not found.
      </div>

      <div v-else class="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card class="lg:col-span-2">
          <CardHeader>
            <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div class="space-y-2">
                <CardTitle class="text-2xl">{{ project.name }}</CardTitle>
                <CardDescription v-if="project.description" class="max-w-prose">
                  {{ project.description }}
                </CardDescription>
              </div>
              <div class="flex flex-col items-start gap-2 text-sm sm:items-end">
                <Badge :variant="projectStatusVariant">
                  {{ projectStatusLabel }}
                </Badge>
                <span class="text-muted-foreground">
                  Uploaded {{ formatDateTime(project.created_at) }}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent v-if="project.github_repo_url || project.secret_link" class="flex flex-col gap-2">
            <p v-if="project.github_repo_url" class="text-sm text-muted-foreground">
              <span class="font-medium text-foreground">GitHub:</span>
              <a class="underline" :href="project.github_repo_url" target="_blank" rel="noopener">
                {{ project.github_repo_url }}
              </a>
            </p>
            <p v-if="project.secret_link" class="text-sm text-muted-foreground break-all">
              <span class="font-medium text-foreground">Secret link:</span>
              {{ project.secret_link }}
            </p>
          </CardContent>
        </Card>

        <Card class="lg:col-span-2">
          <CardHeader class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="space-y-1">
              <CardTitle>Previews</CardTitle>
              <CardDescription>
                Automatically generated assets from the uploaded KiCad archive.
              </CardDescription>
            </div>
            <Button size="sm" @click="goToReview">
              Start review
            </Button>
          </CardHeader>
          <CardContent>
            <div v-if="previewStatus === 'pending'"
              class="flex h-40 items-center justify-center text-sm text-muted-foreground">
              Generating previews…
            </div>
            <div v-else class="space-y-6">
              <ProjectAssetViewer :views="viewerViews" :initial-view-id="schematics.length ? 'schematic' : 'pcb-top'" :show-controls="true" />

              <Card>
                <CardHeader>
                  <CardTitle>Comments</CardTitle>
                </CardHeader>
                <CardContent class="text-sm text-muted-foreground">
                  Comments are available in the review workspace. Click “Start review” above to add or respond to
                  feedback.
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
