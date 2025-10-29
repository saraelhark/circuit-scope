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
import { normaliseStatus, statusVariant, visibilityLabel } from "~/lib/projects"
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

const { data: previewData, status: previewStatus } = useAsyncData<ProjectPreviewResponse>(
  `project-${projectId.value}-previews`,
  () => getProjectPreviews(projectId.value),
  {
    watch: [projectId],
  },
)

const previews = computed(() => previewData.value)

useHead(() => ({
  title: project.value ? `${project.value.name} – Project – Circuit Scope` : "Project – Circuit Scope",
}))

function goBack() {
  router.back()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="space-y-1">
        <Button variant="ghost" class="-ml-2 text-sm" @click="goBack">
          ← Back
        </Button>
        <h1 class="text-3xl font-semibold tracking-tight">Project details</h1>
        <p class="text-muted-foreground">Review the project's metadata and uploaded files.</p>
      </div>

      <div v-if="project" class="flex items-center gap-2">
        <Badge :variant="statusVariant(project.status)">
          {{ normaliseStatus(project.status) }}
        </Badge>
        <span class="text-sm text-muted-foreground">Updated {{ formatDateTime(project.updated_at) }}</span>
      </div>
    </div>

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
            <CardTitle class="text-2xl">{{ project.name }}</CardTitle>
            <CardDescription v-if="project.description" class="max-w-prose">
              {{ project.description }}
            </CardDescription>
          </CardHeader>
          <CardContent class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2">
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Owner:</span>
                {{ project.owner_id }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Visibility:</span>
                {{ visibilityLabel(project) }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Created:</span>
                {{ formatDateTime(project.created_at) }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Updated:</span>
                {{ formatDateTime(project.updated_at) }}
              </p>
            </div>
            <div class="space-y-2">
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
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Status:</span>
                {{ normaliseStatus(project.status) }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Files:</span>
                {{ project.files.length }}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card class="lg:col-span-2">
          <CardHeader>
            <CardTitle>Previews</CardTitle>
            <CardDescription>
              Automatically generated assets from the uploaded KiCad archive.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="previewStatus === 'pending'"
              class="flex h-40 items-center justify-center text-sm text-muted-foreground">
              Generating previews…
            </div>
            <div v-else class="grid gap-6 md:grid-cols-2">
              <div class="space-y-3">
                <h3 class="text-sm font-medium text-muted-foreground">Schematic</h3>
                <div v-if="previews?.schematic" class="overflow-hidden rounded-md border">
                  <img :src="previews.schematic" alt="Schematic preview" class="w-full bg-muted" />
                </div>
                <p v-else class="text-sm text-muted-foreground">Preview not available.</p>
              </div>

              <div class="space-y-3">
                <h3 class="text-sm font-medium text-muted-foreground">PCB layout</h3>
                <div v-if="previews?.layout" class="overflow-hidden rounded-md border">
                  <img :src="previews.layout" alt="PCB layout preview" class="w-full bg-muted" />
                </div>
                <p v-else class="text-sm text-muted-foreground">Preview not available.</p>
              </div>

              <div class="space-y-3 md:col-span-2">
                <h3 class="text-sm font-medium text-muted-foreground">3D view</h3>
                <div v-if="previews?.view3d" class="flex items-center gap-3 text-sm">
                  <a :href="previews.view3d" target="_blank" rel="noopener" class="underline">
                    Download 3D model
                  </a>
                  <span class="text-muted-foreground">(.glb)</span>
                </div>
                <p v-else class="text-sm text-muted-foreground">Preview not available.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="lg:col-span-2">
          <CardHeader>
            <CardTitle>Uploaded files</CardTitle>
            <CardDescription>
              Files associated with this project.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="project.files.length === 0"
              class="rounded-md border border-dashed border-muted-foreground/40 p-6 text-center text-sm text-muted-foreground">
              No files uploaded yet.
            </div>
            <div v-else class="overflow-x-auto">
              <table class="w-full min-w-[560px] text-left text-sm">
                <thead class="border-b border-border text-muted-foreground">
                  <tr class="h-10">
                    <th class="px-3 font-medium">Filename</th>
                    <th class="px-3 font-medium">Type</th>
                    <th class="px-3 font-medium">Stored at</th>
                    <th class="px-3 font-medium">Uploaded</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="file in project.files" :key="file.id" class="border-b border-border/60 last:border-0">
                    <td class="px-3 py-3 font-medium text-foreground">{{ file.filename }}</td>
                    <td class="px-3 py-3 capitalize">{{ file.file_type ?? "unknown" }}</td>
                    <td class="px-3 py-3 text-xs text-muted-foreground break-all">{{ file.storage_path }}</td>
                    <td class="px-3 py-3 text-muted-foreground">{{ formatDateTime(file.created_at) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
