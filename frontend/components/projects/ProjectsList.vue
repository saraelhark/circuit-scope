<script setup lang="ts">
import { computed, reactive } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { formatDateTime } from "~/lib/formatters"
import { normaliseStatus, statusVariant, visibilityLabel } from "~/lib/projects"
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
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-semibold tracking-tight">Projects</h1>
        <p class="text-muted-foreground">Latest KiCad uploads and review status.</p>
      </div>

      <Button>
        <NuxtLink to="/projects/new">New project</NuxtLink>
      </Button>
    </div>

    <div class="flex flex-col gap-4">
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
            <p>Create one to start reviewing your KiCad uploads.</p>
          </div>

          <ul v-else class="grid gap-4">
            <li v-for="project in projects" :key="project.id">
              <Card>
                <CardHeader class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div class="space-y-1">
                    <CardTitle class="text-xl">
                      <NuxtLink :to="`/projects/${project.id}`" class="transition-colors hover:text-primary">
                        {{ project.name }}
                      </NuxtLink>
                    </CardTitle>
                    <CardDescription v-if="project.description" class="max-w-3xl">
                      {{ project.description }}
                    </CardDescription>
                  </div>

                  <div class="flex items-center gap-2">
                    <Badge :variant="statusVariant(project.status)">
                      {{ normaliseStatus(project.status) }}
                    </Badge>
                    <span class="text-sm text-muted-foreground">Updated {{ formatDateTime(project.updated_at) }}</span>
                  </div>
                </CardHeader>

                <CardContent class="grid gap-3 text-sm text-muted-foreground md:grid-cols-2">
                  <div class="space-y-1">
                    <p><span class="font-medium text-foreground">Owner:</span> {{ project.owner_id }}</p>
                    <p>
                      <span class="font-medium text-foreground">Visibility:</span>
                      {{ visibilityLabel(project) }}
                    </p>
                    <p v-if="project.github_repo_url">
                      <span class="font-medium text-foreground">GitHub:</span>
                      <a :href="project.github_repo_url" target="_blank" rel="noopener" class="underline">
                        {{ project.github_repo_url }}
                      </a>
                    </p>
                  </div>
                  <div class="space-y-1">
                    <p>
                      <span class="font-medium text-foreground">Files:</span>
                      {{ project.files.length }}
                    </p>
                    <p>
                      <span class="font-medium text-foreground">Created:</span>
                      {{ formatDateTime(project.created_at) }}
                    </p>
                    <p v-if="project.secret_link">
                      <span class="font-medium text-foreground">Secret link:</span>
                      {{ project.secret_link }}
                    </p>
                  </div>
                </CardContent>

                <CardFooter class="flex items-center justify-end gap-2">
                  <Button variant="secondary" asChild>
                    <NuxtLink :to="`/projects/${project.id}`">View details</NuxtLink>
                  </Button>
                </CardFooter>
              </Card>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="projects.length > 0"
      class="flex flex-col items-center justify-between gap-4 border-t pt-4 text-sm text-muted-foreground md:flex-row">
      <div>
        Showing page {{ pagination.page }} of {{ totalPages }} — {{ total }} project{{ total === 1 ? "" : "s" }}
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
</template>
