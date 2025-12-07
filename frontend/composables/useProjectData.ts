import { computed, watch, onUnmounted, type Ref } from 'vue'
import { useProject } from "~/composables/useProjects"
import type { Project, ProjectPreviewResponse } from "~/types/api/projects"
import { buildViewerViews } from "~/lib/reviewViewer"

export function useProjectData(projectId: Ref<string>) {
    const { getProject, getProjectPreviews } = useProject()

    const { data, error, refresh, status } = useAsyncData<Project>(
        `project-${projectId.value}`,
        () => getProject(projectId.value),
        {
            watch: [projectId],
        },
    )

    const project = computed(() => data.value)

    let pollInterval: NodeJS.Timeout | null = null

    watch(project, (newVal) => {
        if (newVal?.processing_status === "queued" || newVal?.processing_status === "processing") {
            if (!pollInterval) {
                pollInterval = setInterval(() => {
                    refresh()
                }, 2000)
            }
        } else {
            if (pollInterval) {
                clearInterval(pollInterval)
                pollInterval = null
                if (project.value?.processing_status === 'completed') {
                    refreshPreviews()
                }
            }
        }
    }, { immediate: true })

    onUnmounted(() => {
        if (pollInterval) clearInterval(pollInterval)
    })

    const projectStatusLabel = computed(() => {
        const s = project.value?.status
        return s && s.toLowerCase() === "closed" ? "Closed" : "Open"
    })

    const projectStatusVariant = computed(() =>
        projectStatusLabel.value === "Closed" ? "secondary" : "success",
    )

    const totalComments = computed(() => project.value?.total_comment_count ?? 0)
    const openComments = computed(() => project.value?.open_comment_count ?? 0)

    const { data: previewData, status: previewStatus, refresh: refreshPreviews } = useAsyncData<ProjectPreviewResponse>(
        `project-${projectId.value}-previews`,
        () => getProjectPreviews(projectId.value),
        {
            watch: [projectId],
            immediate: false,
        },
    )

    watch(project, (p) => {
        if (p?.processing_status === 'completed' && !previewData.value) {
            refreshPreviews()
        }
    }, { immediate: true })

    const previews = computed(() => previewData.value)
    const schematics = computed(() => previews.value?.schematics ?? [])
    const layouts = computed(() => previews.value?.layouts ?? [])
    const models = computed(() => previews.value?.models ?? [])
    const photos = computed(() => previews.value?.photos ?? [])
    const viewerViews = computed(() => buildViewerViews(schematics.value, layouts.value, models.value))

    return {
        project,
        error,
        refresh,
        status,
        projectStatusLabel,
        projectStatusVariant,
        totalComments,
        openComments,
        previewData,
        previewStatus,
        refreshPreviews,
        schematics,
        layouts,
        models,
        photos,
        viewerViews
    }
}
