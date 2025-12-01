<script setup lang="ts">
import { useTimeAgo } from '@vueuse/core'
import type { Project } from "~/types/api/projects"
import ProjectPreviewThumbnail from "~/components/projects/ProjectPreviewThumbnail.vue"
import ProjectStats from "~/components/projects/ProjectStats.vue"

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
        class="group flex flex-col gap-4 rounded-[8px] border-4 border-white bg-cs-light-green p-4 transition-all hover:brightness-105 sm:flex-row text-white shadow-sm">
        <div class="shrink-0 sm:w-32 md:w-40">
            <div
                class="aspect-square w-full overflow-hidden rounded-md bg-cs-charcoal flex items-center justify-center">
                <ProjectPreviewThumbnail :project-id="project.id" />
            </div>
        </div>

        <div class="flex min-w-0 flex-1 flex-col gap-2">
            <div class="flex items-start justify-between gap-2">
                <div>
                    <h3
                        class="text-lg font-bold leading-tight tracking-tight text-white font-primary group-hover:underline">
                        {{ project.name }}
                    </h3>
                    <p class="mt-1 text-sm text-white/80 line-clamp-2 font-secondary">
                        {{ formattedDescription(project.description) }}
                    </p>
                </div>
            </div>

            <div class="mt-auto">
                <ProjectStats :comment-count="project.total_comment_count" :view-count="project.view_count"
                    :time-ago="timeAgo" />
            </div>
        </div>
    </NuxtLink>
</template>
