<template>
    <div class="min-h-screen bg-background">
        <div class="container py-4">
            <div class="flex flex-col gap-8 lg:flex-row">

                <aside class="w-full lg:w-64 shrink-0 space-y-6">
                    <div>
                        <h2 class="text-lg font-semibold tracking-tight mb-4">My Projects</h2>
                        <nav class="flex flex-col space-y-1">
                            <button v-for="item in navItems" :key="item.id" @click="currentFilter = item.id"
                                class="flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors"
                                :class="currentFilter === item.id ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'">
                                <span class="flex items-center gap-2">
                                    <component :is="item.icon" class="h-4 w-4" />
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
                            <h1 class="text-2xl font-bold tracking-tight">
                                {{navItems.find(i => i.id === currentFilter)?.label}}
                            </h1>
                            <p class="text-muted-foreground">Manage your uploaded designs.</p>
                        </div>
                        <Button asChild>
                            <NuxtLink to="/projects/new">New Project</NuxtLink>
                        </Button>
                    </div>

                    <div class="space-y-4">
                        <div v-if="status === 'pending'" class="py-12 text-center text-muted-foreground">
                            Loading projects...
                        </div>

                        <div v-else-if="filteredProjects.length === 0"
                            class="rounded-lg border border-dashed p-12 text-center">
                            <h3 class="text-lg font-medium">No projects found</h3>
                            <p class="text-muted-foreground mt-1">
                                You don't have any {{ currentFilter === 'all' ? '' : currentFilter }} projects yet.
                            </p>
                        </div>

                        <div v-else class="flex flex-col gap-4">
                            <DashboardProjectItem v-for="project in filteredProjects" :key="project.id"
                                :project="project" @update-status="handleUpdateStatus"
                                @update-metadata="handleUpdateMetadata" />
                        </div>
                    </div>
                </main>

            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { LayoutList, PackageOpen, Archive } from 'lucide-vue-next'
import DashboardProjectItem from "~/components/dashboard/DashboardProjectItem.vue"
import { Button } from "~/components/ui/button"
import { useProject } from "~/composables/useProjects"

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

const projects = computed(() => data.value?.items ?? [])

type FilterType = 'all' | 'open' | 'closed'
const currentFilter = ref<FilterType>('all')

const filteredProjects = computed(() => {
    if (currentFilter.value === 'all') return projects.value
    if (currentFilter.value === 'open') return projects.value.filter(p => p.status === 'open')
    if (currentFilter.value === 'closed') return projects.value.filter(p => p.status === 'closed')
    return projects.value
})

const navItems = computed<{ id: FilterType; label: string; icon: any; count: number }[]>(() => [
    { id: 'all', label: 'All Projects', icon: LayoutList, count: projects.value.length },
    { id: 'open', label: 'Open', icon: PackageOpen, count: projects.value.filter(p => p.status === 'open').length },
    { id: 'closed', label: 'Archived', icon: Archive, count: projects.value.filter(p => p.status === 'closed').length },
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