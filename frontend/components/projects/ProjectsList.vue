<script setup lang="ts">
import { computed } from 'vue'

import ProjectCard from '~/components/projects/ProjectCard.vue'
import { Button } from '~/components/ui/button'
import { Card, CardTitle, CardDescription, CardHeader, CardFooter } from '~/components/ui/card'
import { useProject } from '~/composables/useProjects'
import { usePagination } from '~/composables/usePagination'
import type { ListProjectsQuery, ProjectListResponse } from '~/types/api/projects'

defineOptions({
  name: 'ProjectsList',
})

const { listProjects } = useProject()

const totalItems = ref(0)

const {
  currentPage,
  pageSize,
  totalPages,
  canPrevious,
  canNext,
  goToPrevious,
  goToNext,
} = usePagination(totalItems, { pageSize: 10, initialPage: 1 })

const queryParams = computed<ListProjectsQuery>(() => ({
  page: currentPage.value,
  size: pageSize.value,
  status: 'open',
}))

const { data, error, refresh, status } = useAsyncData<ProjectListResponse>(
  'projects-list',
  () => listProjects(queryParams.value),
  {
    watch: [queryParams],
  },
)

watch(data, (newData) => {
  if (newData) {
    totalItems.value = newData.total
  }
})

const projects = computed(() => data.value?.items ?? [])
</script>

<template>
  <div class="space-y-8">
    <Card
      v-if="error"
      class="bg-cs-card text-white border-cs-border"
    >
      <CardHeader>
        <CardTitle>Failed to load projects</CardTitle>
        <CardDescription class="text-white/80">
          {{ error?.message ?? "Please try again later." }}
        </CardDescription>
      </CardHeader>
      <CardFooter>
        <Button
          variant="secondary"
          @click="refresh"
        >
          Retry
        </Button>
      </CardFooter>
    </Card>

    <div v-else>
      <div
        v-if="status === 'pending'"
        class="flex h-32 items-center justify-center text-white font-primary"
      >
        Loading projects…
      </div>

      <div v-else>
        <div
          v-if="projects.length === 0"
          class="flex h-48 flex-col items-center justify-center rounded-lg border border-dashed border-white/30 p-6 text-center text-white/60 font-primary"
        >
          <p class="text-lg mb-2">
            No projects yet.
          </p>
          <p class="text-sm mb-4">
            Be the first to upload your design!
          </p>
          <NuxtLink to="/projects/new">
            <Button variant="cta">
              Upload Project
            </Button>
          </NuxtLink>
        </div>

        <div
          v-else
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
        >
          <ProjectCard
            v-for="project in projects"
            :key="project.id"
            :project="project"
          />
        </div>
      </div>
    </div>

    <div
      v-if="projects.length > 0"
      class="flex flex-col items-center justify-between gap-4 pt-4 text-sm text-white/80 md:flex-row font-secondary"
    >
      <div>
        Showing page {{ currentPage }} of {{ totalPages }}
      </div>
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="!canPrevious"
          class="border-cs-border text-white hover:bg-cs-card hover:border-cs-brand bg-transparent"
          @click="goToPrevious"
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          :disabled="!canNext"
          class="border-cs-border text-white hover:bg-cs-card hover:border-cs-brand bg-transparent"
          @click="goToNext"
        >
          Next
        </Button>
      </div>
    </div>
  </div>
</template>
