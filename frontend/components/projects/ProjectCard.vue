<script setup lang="ts">
import { MessageSquare } from 'lucide-vue-next'
import { useTimeAgo } from '@vueuse/core'
import type { Project } from "~/types/api/projects"
import ProjectPreviewThumbnail from "~/components/projects/ProjectPreviewThumbnail.vue"

const props = defineProps<{
    project: Project
}>()

const timeAgo = useTimeAgo(() => new Date(props.project.created_at))

const MAX_DESCRIPTION_LENGTH = 120

function formattedDescription(description: string | null) {
    const desc = description?.trim()
    if (!desc) return ""
    if (desc.length <= MAX_DESCRIPTION_LENGTH) {
        return desc
    }
    return `${desc.slice(0, MAX_DESCRIPTION_LENGTH).trimEnd()}…`
}
</script>

<template>
    <NuxtLink :to="`/projects/${project.id}`"
        class="group flex flex-col gap-4 rounded-lg border p-4 transition-all hover:border-primary/50 sm:flex-row bg-card text-card-foreground shadow-sm">
        <!-- Thumbnail -->
        <div class="shrink-0 sm:w-32 md:w-40">
            <div class="aspect-square w-full overflow-hidden rounded-md border bg-muted">
                <ProjectPreviewThumbnail :project-id="project.id" />
            </div>
        </div>

        <!-- Content -->
        <div class="flex min-w-0 flex-1 flex-col gap-2">
            <div class="flex items-start justify-between gap-2">
                <div>
                    <h3
                        class="text-lg font-semibold leading-tight tracking-tight text-foreground group-hover:text-primary">
                        {{ project.name }}
                    </h3>
                    <p class="mt-1 text-sm text-muted-foreground line-clamp-2">
                        {{ formattedDescription(project.description) }}
                    </p>
                </div>
            </div>

            <div class="flex items-center gap-4 text-xs text-muted-foreground mt-auto">
                <div class="flex items-center gap-1">
                    <MessageSquare class="h-3.5 w-3.5" />
                    <span>{{ project.comments_count || 0 }}</span>
                </div>
                <span>{{ timeAgo }}</span>
            </div>
        </div>
    </NuxtLink>
</template>