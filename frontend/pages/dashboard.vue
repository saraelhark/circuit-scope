<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import DashboardProjectItem from "~/components/dashboard/DashboardProjectItem.vue"
import { Button } from "~/components/ui/button"
import { useProject } from "~/composables/useProjects"

import { usePagination } from "~/composables/usePagination"

definePageMeta({
    middleware: 'auth'
})

useHead({
    title: "Dashboard - Circuit Scope",
})

const { backendUser } = useBackendUser()
const { listProjects, updateProject } = useProject()

const { data, status, refresh } = useAsyncData(
    'my-projects',
    () => listProjects({
        owner_id: backendUser.value?.id,
        size: 100
    }),
    {
        watch: [backendUser],
        immediate: !!backendUser.value?.id
    }
)

const projects = computed(() => {
    const items = data.value?.items ?? []
    return [...items].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

type FilterType = 'all' | 'open' | 'closed'
const currentFilter = ref<FilterType>('all')

const filteredProjects = computed(() => {
    if (currentFilter.value === 'all') return projects.value
    if (currentFilter.value === 'open') return projects.value.filter(p => p.status === 'open')
    if (currentFilter.value === 'closed') return projects.value.filter(p => p.status === 'closed')
    return projects.value
})

const filteredProjectsCount = computed(() => filteredProjects.value.length)

const {
    currentPage,
    totalPages,
    pageSize,
    canPrevious,
    canNext,
    goToPrevious,
    goToNext,
    paginateArray
} = usePagination(filteredProjectsCount, { pageSize: 5 })

const paginatedProjects = computed(() => paginateArray(filteredProjects.value))

watch(filteredProjects, () => {
    if (currentPage.value > totalPages.value) {
        currentPage.value = totalPages.value
    }
})

const navItems = computed<{ id: FilterType; label: string; iconClass: string; count: number }[]>(() => [
    { id: 'all', label: 'All Projects', iconClass: 'fas fa-list', count: projects.value.length },
    { id: 'open', label: 'Open', iconClass: 'fas fa-box-open', count: projects.value.filter(p => p.status === 'open').length },
    { id: 'closed', label: 'Archived', iconClass: 'fas fa-archive', count: projects.value.filter(p => p.status === 'closed').length },
])

async function handleUpdateStatus(id: string, newStatus: string) {
    try {
        await updateProject(id, { status: newStatus })
        await refresh()
    } catch (e) {
        console.error('Failed to update status', e)
    }
}

async function handleUpdateMetadata(id: string, payload: { name?: string | null; description?: string | null }) {
    try {
        await updateProject(id, payload)
        await refresh()
    } catch (e) {
        console.error('Failed to update project metadata', e)
    }
}
</script>

<template>
    <div
        class="min-h-[calc(100vh-3.5rem)] container px-4 sm:px-8 py-8 max-w-6xl mx-auto bg-cs-light-green border-x-4 border-y-0 border-white text-white">
        <div class="flex flex-col gap-8 lg:flex-row">

            <aside class="w-full lg:w-64 shrink-0 space-y-6">
                <div>
                    <h2 class="text-lg font-semibold tracking-tight mb-4 text-white font-primary">My Projects</h2>
                    <nav class="flex flex-col space-y-1">
                        <button v-for="item in navItems" :key="item.id" @click="currentFilter = item.id"
                            class="flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors"
                            :class="currentFilter === item.id ? 'bg-white/15 text-white' : 'text-white/70 hover:bg-white/10 hover:text-white'">
                            <span class="flex items-center gap-2">
                                <i :class="[item.iconClass, 'h-4 w-4']"></i>
                                {{ item.label }}
                            </span>
                            <span v-if="item.count !== undefined" class="text-xs opacity-70">{{ item.count }}</span>
                        </button>
                    </nav>
                </div>
            </aside>

            <main class="flex-1 space-y-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h1 class="text-2xl font-bold tracking-tight text-white font-primary">
                            {{navItems.find(i => i.id === currentFilter)?.label}}
                        </h1>
                        <p class="text-white/80 font-secondary">Manage your projects.</p>
                    </div>
                </div>

                <div class="space-y-4">
                    <div v-if="status === 'pending'" class="py-12 text-center text-white/80">
                        Loading projects...
                    </div>

                    <div v-else-if="filteredProjects.length === 0"
                        class="rounded-lg border border-dashed border-white/50 p-12 text-center text-white">
                        <h3 class="text-lg font-medium font-primary">No projects found</h3>
                        <p class="mt-1 text-white/80 font-secondary">
                            You don't have any {{ currentFilter === 'all' ? '' : currentFilter }} projects yet.
                        </p>
                    </div>

                    <div v-else class="flex flex-col gap-4">
                        <DashboardProjectItem v-for="project in paginatedProjects" :key="project.id" :project="project"
                            @update-status="handleUpdateStatus" @update-metadata="handleUpdateMetadata" />
                    </div>

                    <div v-if="filteredProjects.length > pageSize"
                        class="flex flex-col items-center justify-between gap-4 pt-4 text-sm text-white/80 md:flex-row font-secondary">
                        <div>
                            Showing page {{ currentPage }} of {{ totalPages }}
                        </div>
                        <div class="flex items-center gap-2">
                            <Button variant="regular" size="sm" :disabled="!canPrevious" @click="goToPrevious">
                                Previous
                            </Button>
                            <Button variant="regular" size="sm" :disabled="!canNext" @click="goToNext">
                                Next
                            </Button>
                        </div>
                    </div>
                </div>
            </main>

        </div>
    </div>
</template>
