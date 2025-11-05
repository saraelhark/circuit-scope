<script setup lang="ts">
import { computed, ref } from 'vue'
import { ExternalLink, Archive, RefreshCw, Calendar, Clock, Share2, Pencil } from 'lucide-vue-next'
import { useTimeAgo } from '@vueuse/core'
import { Button } from "~/components/ui/button"
import { Badge } from "~/components/ui/badge"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { Textarea } from "~/components/ui/textarea"
import { formatDateTime } from "~/lib/formatters"
import { normaliseStatus, statusVariant } from "~/lib/projects"
import type { Project } from "~/types/api/projects"
import ProjectPreviewThumbnail from "~/components/projects/ProjectPreviewThumbnail.vue"

const props = defineProps<{
    project: Project
}>()

const emit = defineEmits<{
    (e: 'update-status', id: string, status: string): void
    (e: 'update-metadata', id: string, payload: { name?: string | null; description?: string | null }): void
}>()

const timeAgo = useTimeAgo(() => new Date(props.project.updated_at))
const isArchived = computed(() => props.project.status === 'closed')

const isEditing = ref(false)
const editName = ref(props.project.name)
const editDescription = ref(props.project.description ?? '')

function toggleStatus() {
    const newStatus = isArchived.value ? 'open' : 'closed'
    emit('update-status', props.project.id, newStatus)
}

function startEdit() {
    isEditing.value = true
    editName.value = props.project.name
    editDescription.value = props.project.description ?? ''
}

function cancelEdit() {
    isEditing.value = false
    editName.value = props.project.name
    editDescription.value = props.project.description ?? ''
}

function saveEdit() {
    emit('update-metadata', props.project.id, {
        name: editName.value,
        description: editDescription.value || null,
    })
    isEditing.value = false
}

async function shareProject() {
    if (!import.meta.client) return

    try {
        const origin = window.location.origin
        const url = `${origin}/projects/${props.project.id}`

        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(url)
        } else {
            console.warn('Clipboard API not available. Could not copy project link automatically.', url)
        }
    } catch (error) {
        console.error('Failed to copy project link', error)
    }
}
</script>

<template>
    <div
        class="flex flex-col gap-4 rounded-lg border bg-card p-4 transition-colors hover:bg-accent/5 sm:flex-row sm:items-center sm:justify-between">

        <!-- Left: Info & Thumbnail -->
        <div class="flex flex-1 items-start gap-4">
            <!-- Thumbnail -->
            <div class="h-16 w-16 shrink-0 overflow-hidden rounded-md border bg-muted">
                <ProjectPreviewThumbnail :project-id="project.id" />
            </div>

            <!-- Details -->
            <div class="flex flex-col gap-1">
                <div class="flex items-center gap-2">
                    <h3 class="font-semibold leading-none tracking-tight text-foreground">
                        <NuxtLink :to="`/projects/${project.id}`" class="hover:underline">
                            {{ project.name }}
                        </NuxtLink>
                    </h3>
                    <Badge :variant="statusVariant(project.status)" class="h-5 px-1.5 capitalize">
                        {{ normaliseStatus(project.status) }}
                    </Badge>
                </div>

                <div class="flex flex-col gap-1 text-xs text-muted-foreground sm:flex-row sm:items-center sm:gap-4">
                    <div class="flex items-center gap-1">
                        <Calendar class="h-3.5 w-3.5" />
                        <span>Posted on {{ formatDateTime(project.created_at, undefined, {
                            dateStyle: 'medium',
                            timeStyle: undefined
                        }) }}</span>
                    </div>
                    <div class="hidden sm:block">•</div>
                    <div class="flex items-center gap-1">
                        <Clock class="h-3.5 w-3.5" />
                        <span>Active {{ timeAgo }}</span>
                    </div>
                </div>

                <div v-if="isEditing" class="mt-3 flex flex-col gap-3 max-w-md">
                    <div class="space-y-1">
                        <Label :for="`project-${project.id}-name`">Title</Label>
                        <Input :id="`project-${project.id}-name`" v-model="editName" />
                    </div>
                    <div class="space-y-1">
                        <Label :for="`project-${project.id}-description`">Description</Label>
                        <Textarea :id="`project-${project.id}-description`" v-model="editDescription" rows="3" />
                    </div>
                    <div class="flex items-center gap-2">
                        <Button size="sm" class="h-8 px-3" @click="saveEdit">
                            Save
                        </Button>
                        <Button variant="ghost" size="sm" class="h-8 px-3" @click="cancelEdit">
                            Cancel
                        </Button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right: Actions -->
        <div class="flex items-center gap-2 sm:self-center">
            <Button variant="outline" size="sm" asChild class="h-9">
                <NuxtLink :to="`/projects/${project.id}`">
                    <ExternalLink class="mr-2 h-4 w-4" />
                    View
                </NuxtLink>
            </Button>

            <Button variant="outline" size="sm" class="h-9" @click="shareProject">
                <Share2 class="mr-2 h-4 w-4" />
                Share
            </Button>

            <Button variant="outline" size="sm" class="h-9" @click="startEdit">
                <Pencil class="mr-2 h-4 w-4" />
                Edit
            </Button>

            <Button variant="outline" size="sm" class="h-9"
                :class="isArchived ? 'text-primary hover:text-primary' : 'text-muted-foreground hover:text-foreground'"
                @click="toggleStatus">
                <template v-if="isArchived">
                    <RefreshCw class="mr-2 h-4 w-4" />
                    Re-open
                </template>
                <template v-else>
                    <Archive class="mr-2 h-4 w-4" />
                    Archive
                </template>
            </Button>
        </div>
    </div>
</template>
