<script setup lang="ts">
import { computed, reactive } from "vue"

import ProjectCard from "~/components/projects/ProjectCard.vue"
import { Button } from "~/components/ui/button"
import { Card, CardTitle, CardDescription, CardHeader, CardFooter } from "~/components/ui/card"
import { useProject } from "~/composables/useProjects"
import type { ListProjectsQuery, ProjectListResponse } from "~/types/api/projects"

defineOptions({
  name: "ProjectsList",
})
const pagination = reactive({
  page: 1,
  size: 10,
})

const queryParams = computed<ListProjectsQuery>(() => ({
  page: pagination.page,
  size: pagination.size,
}))

const { listProjects } = useProject()

const { data, error, refresh, status } = useAsyncData<ProjectListResponse>(
  "projects-list",
  () => listProjects(queryParams.value),
  {
    watch: [queryParams],
  },
)

const projects = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => {
  if (!data.value || data.value.size <= 0) {
    return 1
  }
  return Math.max(1, Math.ceil(data.value.total / data.value.size))
})

const canPrevious = computed(() => pagination.page > 1)
const canNext = computed(() => pagination.page < totalPages.value)

function goToPrevious() {
  if (canPrevious.value) {
    pagination.page -= 1
  }
}

function goToNext() {
  if (canNext.value) {
    pagination.page += 1
  }
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Latest Projects</h1>
        <p class="text-muted-foreground">Discover and review the latest hardware schematics/layouts designs.</p>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div class="lg:col-span-2 space-y-6">
        <Card v-if="error">
          <CardHeader>
            <CardTitle>Failed to load projects</CardTitle>
            <CardDescription>{{ error?.message ?? "Please try again later." }}</CardDescription>
          </CardHeader>
          <CardFooter>
            <Button variant="secondary" @click="refresh">
              Retry
            </Button>
          </CardFooter>
        </Card>

        <div v-else>
          <div v-if="status === 'pending'" class="flex h-32 items-center justify-center text-muted-foreground">
            Loading projects…
          </div>

          <div v-else>
            <div v-if="projects.length === 0"
              class="flex h-32 flex-col items-center justify-center rounded-lg border border-dashed border-muted-foreground/30 p-6 text-center text-sm text-muted-foreground">
              <p>No projects yet.</p>
              <p>Be the first to upload your design!</p>
            </div>

            <div v-else class="flex flex-col gap-4">
              <ProjectCard v-for="project in projects" :key="project.id" :project="project" />
            </div>
          </div>
        </div>

        <div v-if="projects.length > 0"
          class="flex flex-col items-center justify-between gap-4 pt-4 text-sm text-muted-foreground md:flex-row">
          <div>
            Showing page {{ pagination.page }} of {{ totalPages }}
          </div>
          <div class="flex items-center gap-2">
            <Button variant="outline" size="sm" :disabled="!canPrevious" @click="goToPrevious">
              Previous
            </Button>
            <Button variant="outline" size="sm" :disabled="!canNext" @click="goToNext">
              Next
            </Button>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div class="p-6 space-y-4">
            <h3 class="font-semibold leading-none tracking-tight">Submit your project</h3>
            <p class="text-sm text-muted-foreground">
              Get feedback on your schematic and PCB layout from the community.
            </p>
            <Button class="w-full" asChild>
              <NuxtLink to="/projects/new">Upload Project</NuxtLink>
            </Button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
