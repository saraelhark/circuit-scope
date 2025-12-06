<script setup lang="ts">
import { computed, reactive, ref, watch, onMounted } from "vue"

import { type ViewerView } from "~/types/viewer"
import ReviewCanvas, {
    type ViewerAnnotation,
    type CircleViewerAnnotation,
} from "~/components/projects/ReviewCanvas.vue"
import ReviewCanvasToolbar from "~/components/projects/ReviewCanvasToolbar.vue"
import ReviewCommentsSidebar from "~/components/projects/ReviewCommentsSidebar.vue"
import AuthChoiceModal from "~/components/projects/AuthChoiceModal.vue"
import { useProject } from "~/composables/useProjects"
import { useCommentThreads } from "~/composables/useCommentThreads"
import { generateAlias } from "~/lib/alias"
import { buildReviewViews } from "~/lib/reviewViewer"
import { mapThreadsToAnnotations } from "~/lib/reviewAnnotations"
import type { AnnotationTool, CommentThread, ThreadAnnotation } from "~/types/api/commentThreads"
import type { Project, ProjectPreviewResponse } from "~/types/api/projects"

definePageMeta({
    layout: false,
})

const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.id as string)

const { getProject, getProjectPreviews } = useProject()
const { listThreads, createThread, addComment, updateThreadResolution } = useCommentThreads()

const { status } = useAuth()
const { backendUser } = useBackendUser()

const anonAlias = useCookie<string | null>("cs_anon_alias", { default: () => null })

function getAnonAlias(): string {
    if (!anonAlias.value) {
        anonAlias.value = generateAlias()
    }
    return anonAlias.value as string
}

const { data: projectData } = useAsyncData<Project>(
    () => getProject(projectId.value),
    {
        watch: [projectId],
    },
)

const { data: previewData } = useAsyncData<ProjectPreviewResponse>(
    () => getProjectPreviews(projectId.value),
    {
        watch: [projectId],
    },
)

const project = computed(() => projectData.value)
const previews = computed(() => previewData.value)

const schematics = computed(() => previews.value?.schematics ?? [])
const layouts = computed(() => previews.value?.layouts ?? [])
const models = computed(() => previews.value?.models ?? [])
const photos = computed(() => previews.value?.photos ?? [])

const sourceType = computed(
    () => (project.value as any)?.source_type as string | undefined,
)

const projectOwnerId = computed(
    () => (project.value as any)?.owner_id as string | undefined,
)
const canResolveThreads = computed(
    () => status.value === "authenticated" && !!backendUser.value?.id && backendUser.value.id === projectOwnerId.value,
)

const viewerViews = computed<ViewerView[]>(() =>
    buildReviewViews(sourceType.value, schematics.value, layouts.value, models.value, photos.value),
)

const {
    data: threadData,
    status: threadStatus,
    refresh: refreshThreads,
} = useAsyncData(
    () => listThreads(projectId.value),
    {
        watch: [projectId],
    },
)

const threads = computed(() => threadData.value?.items ?? [])
const threadStatusComputed = computed(() => threadStatus.value)

const viewAnnotations = computed<Record<string, ViewerAnnotation[]>>(() =>
    mapThreadsToAnnotations(threads.value),
)

const activeThreadId = ref<string | null>(null)
const activeThread = computed(() =>
    threads.value.find((thread) => thread.id === activeThreadId.value) ?? null,
)

watch(threads, (current) => {
    if (!current.length) {
        activeThreadId.value = null
        return
    }

    const threadFromQuery = route.query.thread as string
    if (threadFromQuery && current.some(t => t.id === threadFromQuery)) {
        if (activeThreadId.value !== threadFromQuery) {
            activeThreadId.value = threadFromQuery
            const thread = current.find(t => t.id === threadFromQuery)
            if (thread?.view_id) {
                setActiveView(thread.view_id)
            }
        }
        return
    }

    if (!current.some((thread) => thread.id === activeThreadId.value)) {
        activeThreadId.value = current[0].id
    }
})

watch(() => route.query.thread, (newThreadId) => {
    if (newThreadId && typeof newThreadId === 'string') {
        const thread = threads.value.find(t => t.id === newThreadId)
        if (thread) {
            activeThreadId.value = thread.id
            if (thread.view_id) {
                setActiveView(thread.view_id)
            }
        }
    }
})

const selectedTool = ref<'pan' | 'circle'>('pan')

type ShapeCreatedPayload = { viewId: string } & CircleViewerAnnotation

function handleShapeCreated(payload: ShapeCreatedPayload) {
    pendingPin.value = {
        viewId: payload.viewId,
        x: payload.pinX,
        y: payload.pinY,
        tool: payload.tool,
        data: payload.data,
    }
    formError.value = null
    newThreadForm.content = ""
}
const currentViewId = ref<string>("schematic")
const pendingPin = ref<{
    viewId: string
    x: number
    y: number
    tool: AnnotationTool
    data: CircleAnnotationData
} | null>(null)

watch(viewerViews, (views) => {
    if (!views.length) return
    if (!views.some((view) => view.id === currentViewId.value)) {
        currentViewId.value = views[0].id
    }
})

type CircleAnnotationData = CircleViewerAnnotation['data']
const newThreadForm = reactive({
    content: "",
})

const replyForm = reactive({
    content: "",
})

const formError = ref<string | null>(null)
const replyError = ref<string | null>(null)

const showAuthModal = ref(false)
const authModalContext = ref<"thread" | "reply" | null>(null)

function setActiveView(viewId: string) {
    if (currentViewId.value === viewId) {
        viewer.value?.setActiveView(viewId)
        return
    }
    currentViewId.value = viewId
    viewer.value?.setActiveView(viewId)
}

function openThread(thread: CommentThread) {
    activeThreadId.value = thread.id
    if (thread.view_id) {
        setActiveView(thread.view_id)
    }
}

function selectTool(tool: 'pan' | 'circle') {
    selectedTool.value = tool
}

function cancelPendingPin() {
    pendingPin.value = null
    formError.value = null
}


async function submitNewThread() {
    if (!pendingPin.value) {
        formError.value = "Click on the canvas to place a pin first."
        return
    }
    if (!newThreadForm.content.trim()) {
        formError.value = "Comment content is required."
        return
    }

    formError.value = null

    if (status.value === "authenticated" && backendUser.value?.id) {
        await createThreadAsAuthenticated()
        return
    }

    authModalContext.value = "thread"
    getAnonAlias()
    showAuthModal.value = true
}

async function createThreadAsAuthenticated() {
    if (!pendingPin.value || !backendUser.value?.id) return

    const annotation: ThreadAnnotation = {
        tool: pendingPin.value.tool,
        data: pendingPin.value.data,
    }

    const payload = {
        view_id: pendingPin.value.viewId,
        pin_x: pendingPin.value.x,
        pin_y: pendingPin.value.y,
        annotation,
        initial_comment: {
            content: newThreadForm.content,
            author_id: backendUser.value.id,
        },
    }

    const created = await createThread(projectId.value, payload)
    newThreadForm.content = ""
    pendingPin.value = null
    activeThreadId.value = created.id
    await refreshThreads()
}

async function createThreadAsAnonymous() {
    if (!pendingPin.value) return

    const alias = getAnonAlias()

    const annotation: ThreadAnnotation = {
        tool: pendingPin.value.tool,
        data: pendingPin.value.data,
    }

    const payload = {
        view_id: pendingPin.value.viewId,
        pin_x: pendingPin.value.x,
        pin_y: pendingPin.value.y,
        annotation,
        initial_comment: {
            content: newThreadForm.content,
            guest_name: alias,
        },
    }

    const created = await createThread(projectId.value, payload)
    newThreadForm.content = ""
    pendingPin.value = null
    activeThreadId.value = created.id
    await refreshThreads()
}

async function submitReply() {
    const thread = activeThread.value
    if (!thread) {
        replyError.value = "Select a thread first."
        return
    }
    if (!replyForm.content.trim()) {
        replyError.value = "Reply content is required."
        return
    }
    replyError.value = null

    if (status.value === "authenticated" && backendUser.value?.id) {
        await submitReplyAsAuthenticated()
        return
    }

    authModalContext.value = "reply"
    getAnonAlias()
    showAuthModal.value = true
}

async function submitReplyAsAuthenticated() {
    const thread = activeThread.value
    if (!thread || !backendUser.value?.id) return

    await addComment(projectId.value, thread.id, {
        content: replyForm.content,
        author_id: backendUser.value.id,
        parent_id: null,
    })

    replyForm.content = ""
    await refreshThreads()
}

async function submitReplyAsAnonymous() {
    const thread = activeThread.value
    if (!thread) return

    const alias = getAnonAlias()

    await addComment(projectId.value, thread.id, {
        content: replyForm.content,
        author_id: null,
        parent_id: null,
        guest_name: alias,
    })

    replyForm.content = ""
    await refreshThreads()
}

async function continueAsAnonymous() {
    if (authModalContext.value === "thread") {
        await createThreadAsAnonymous()
    } else if (authModalContext.value === "reply") {
        await submitReplyAsAnonymous()
    }
    showAuthModal.value = false
    authModalContext.value = null
}

function goToLogin() {
    showAuthModal.value = false
    authModalContext.value = null
    router.push("/login")
}

function cancelAuthModal() {
    showAuthModal.value = false
    authModalContext.value = null
}

async function toggleThreadResolution(thread: CommentThread) {
    await updateThreadResolution(projectId.value, thread.id, {
        is_resolved: !thread.is_resolved,
        resolved_by_id: null,
    })
    await refreshThreads()
}


const sidebarOpen = ref(true)
function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
}
const viewer = ref<InstanceType<typeof ReviewCanvas> | null>(null)
function zoomIn() { viewer.value?.adjustZoom(1) }
function zoomOut() { viewer.value?.adjustZoom(-1) }
function resetZoom() { viewer.value?.resetView() }
function flipModel() { viewer.value?.flipModel() }
const isMobile = ref(false)

onMounted(() => {
    if (typeof window !== "undefined") {
        isMobile.value = window.innerWidth < 768
    }
    if (isMobile.value) {
        sidebarOpen.value = false
    }

    watch(currentViewId, (viewId) => {
        if (viewer.value && viewId) {
            viewer.value.setActiveView(viewId)
        }
    }, { immediate: true })
})
</script>

<template>
    <header class="sticky top-0 z-50 w-full bg-cs-lighter-green text-cs-charcoal font-primary">
        <div class="container px-8 sm:px-16 flex h-14 items-center justify-between">
            <div class="flex items-center gap-4">
                <NuxtLink to="/"
                    class="flex items-center gap-2 text-xl font-bold text-cs-charcoal hover:opacity-80 transition-opacity">
                    <img class="h-8 w-8 rounded-lg" src="/logo.svg" alt="Circuit Scope logo" />
                    <span class="ml-4 text-cs-dark-green hidden sm:block">Circuit Scope</span>
                </NuxtLink>
            </div>


            <div class="flex items-center gap-2">

            </div>
        </div>
    </header>
    <div class="flex h-screen supports-[height:100dvh]:h-[100dvh] w-full overflow-hidden relative">

        <div class="relative flex-1 bg-neutral-50 dark:bg-neutral-900 w-full h-full">
            <ReviewCanvasToolbar :views="viewerViews" :current-view-id="currentViewId" :selected-tool="selectedTool"
                @select-view="setActiveView" @select-tool="selectTool" @zoom-in="zoomIn" @zoom-out="zoomOut"
                @reset-zoom="resetZoom" @flip-view="flipModel" />

            <ReviewCanvas ref="viewer" class="h-full w-full" :views="viewerViews" :initial-view-id="currentViewId"
                :active-tool="selectedTool" :annotations="viewAnnotations" @view-change="setActiveView"
                @shape-created="handleShapeCreated">
                <template #overlay="slotProps">
                    <component :is="{ ...slotProps }" />
                </template>
            </ReviewCanvas>

            <button v-if="!sidebarOpen" @click="toggleSidebar"
                class="absolute right-0 top-1/2 z-30 -translate-y-1/2 rounded-l-md border bg-card px-1 py-2 text-xs hidden lg:block shadow-md">
                &lt;
            </button>

            <button v-if="!sidebarOpen" @click="toggleSidebar"
                class="absolute right-4 bottom-4 z-30 rounded-full h-12 w-12 flex items-center justify-center border bg-primary text-primary-foreground shadow-lg lg:hidden">
                <i class="fas fa-comment-alt text-xl"></i>
            </button>
        </div>

        <div v-if="sidebarOpen && isMobile" class="fixed inset-0 bg-black/50 z-40 lg:hidden"
            @click="sidebarOpen = false"></div>

        <aside v-if="sidebarOpen"
            class="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-card border-l shadow-xl transition-transform duration-200 lg:relative lg:translate-x-0 lg:shadow-none lg:z-auto shrink-0 flex flex-col">

            <button @click="toggleSidebar"
                class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full rounded-l-md border bg-card p-2 text-xs hidden lg:block shadow-md">
                &gt;
            </button>

            <div class="flex items-center justify-between p-4 border-b lg:hidden">
                <h3 class="font-semibold">Comments</h3>
                <button @click="toggleSidebar" class="p-2 hover:bg-accent rounded-md">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <div class="flex-1 overflow-hidden p-4">
                <ReviewCommentsSidebar :threads="threads" :active-thread-id="activeThreadId"
                    :thread-status="threadStatusComputed" :pending-pin-present="!!pendingPin" :form-error="formError"
                    :reply-error="replyError" :new-thread-content="newThreadForm.content"
                    :reply-content="replyForm.content" @update:newThreadContent="newThreadForm.content = $event"
                    @update:replyContent="replyForm.content = $event" @open-thread="openThread"
                    @submit-new-thread="submitNewThread" @cancel-pending-pin="cancelPendingPin"
                    @submit-reply="submitReply" @toggle-thread-resolution="toggleThreadResolution"
                    :can-resolve-threads="canResolveThreads" />
            </div>
        </aside>
    </div>

    <AuthChoiceModal :open="showAuthModal" :alias="anonAlias" @continue-anonymous="continueAsAnonymous"
        @sign-in="goToLogin" @cancel="cancelAuthModal" />
</template>
