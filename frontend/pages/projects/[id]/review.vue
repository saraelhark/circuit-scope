<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import { Input } from "~/components/ui/input"
import { Textarea } from "~/components/ui/textarea"
import ReviewCanvas, {
    type ViewerView,
    type ViewerAnnotation,
    type CircleViewerAnnotation,
    type ArrowViewerAnnotation,
} from "~/components/projects/ReviewCanvas.vue"
import { formatDateTime } from "~/lib/formatters"
import { useProject } from "~/composables/useProjects"
import { useCommentThreads } from "~/composables/useCommentThreads"
import type { AnnotationTool, CommentThread, ThreadAnnotation } from "~/types/api/commentThreads"
import type { Project, ProjectPreviewResponse } from "~/types/api/projects"

definePageMeta({
    layout: false,
})

const route = useRoute()

const projectId = computed(() => route.params.id as string)

const { getProjectPreviews } = useProject()
const { listThreads, createThread, addComment, updateThreadResolution } = useCommentThreads()


const { data: previewData } = useAsyncData<ProjectPreviewResponse>(
    () => getProjectPreviews(projectId.value),
    {
        watch: [projectId],
    },
)

const previews = computed(() => previewData.value)

const schematics = computed(() => previews.value?.schematics ?? [])
const layouts = computed(() => previews.value?.layouts ?? [])

const viewerViews = computed<ViewerView[]>(() => {
    const views: ViewerView[] = []

    if (schematics.value.length) {
        views.push({
            id: "schematic",
            label: "Schematic",
            asset: schematics.value[0],
            fallbackMessage: "No schematic SVG generated yet.",
        })
    } else {
        views.push({
            id: "schematic",
            label: "Schematic",
            asset: undefined,
            fallbackMessage: "No schematic previews available.",
        })
    }

    const topLayout = layouts.value.find((layout) => /top|front/i.test(layout.title ?? layout.id)) ?? layouts.value[0]
    const bottomLayout = layouts.value.find((layout) => /bottom|back/i.test(layout.title ?? layout.id))

    views.push({
        id: "pcb-top",
        label: "PCB Top",
        asset: topLayout ?? null,
        fallbackMessage: layouts.value.length
            ? "No top-side layout detected; showing first layout available."
            : "No PCB layout previews available.",
    })

    views.push({
        id: "pcb-bottom",
        label: "PCB Bottom",
        asset: bottomLayout ?? (layouts.value.length > 1 ? layouts.value[1] : null),
        fallbackMessage: layouts.value.length > 1
            ? "No bottom-side layout detected; showing alternative layout."
            : "No additional PCB layout previews available.",
    })

    return views
})

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

const viewAnnotations = computed<Record<string, ViewerAnnotation[]>>(() => {
    const map: Record<string, ViewerAnnotation[]> = {}
    for (const thread of threads.value) {
        const annotation = thread.annotation
        if (!annotation || annotation.tool === "pin") continue

        const entry: ViewerAnnotation | null = (() => {
            if (annotation.tool === "circle") {
                const radius = Number(annotation.data?.radius ?? 0)
                if (!Number.isFinite(radius) || radius <= 0) return null
                return {
                    id: thread.id,
                    tool: "circle",
                    pinX: thread.pin_x,
                    pinY: thread.pin_y,
                    data: { radius },
                }
            }
            if (annotation.tool === "arrow") {
                const targetX = Number(annotation.data?.target_x)
                const targetY = Number(annotation.data?.target_y)
                if (!Number.isFinite(targetX) || !Number.isFinite(targetY)) return null
                return {
                    id: thread.id,
                    tool: "arrow",
                    pinX: thread.pin_x,
                    pinY: thread.pin_y,
                    data: { target_x: targetX, target_y: targetY },
                }
            }
            return null
        })()

        if (!entry) continue

        if (!map[thread.view_id]) {
            map[thread.view_id] = []
        }
        map[thread.view_id].push(entry)
    }
    return map
})

const activeThreadId = ref<string | null>(null)
const activeThread = computed(() =>
    threads.value.find((thread) => thread.id === activeThreadId.value) ?? null,
)

watch(threads, (current) => {
    if (!current.length) {
        activeThreadId.value = null
        return
    }

    if (!current.some((thread) => thread.id === activeThreadId.value)) {
        activeThreadId.value = current[0].id
    }
})

// active drawing/pan tool
const selectedTool = ref<'pan' | 'circle' | 'arrow'>('pan')

type ShapeCreatedPayload =
    | ({ viewId: string } & CircleViewerAnnotation)
    | ({ viewId: string } & ArrowViewerAnnotation)

/** Handle shape completion from canvas */
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
// removed old selectedTool definition
// no placementTool required under new drawing model
const pendingPin = ref<{
    viewId: string
    x: number
    y: number
    tool: Extract<AnnotationTool, 'circle' | 'arrow'>
    data: CircleAnnotationData | ArrowAnnotationData
} | null>(null)
// arrow target stored inside pendingPin data now
// placementMessage no longer used

const toolOptions: { label: string; value: 'pan' | 'circle' | 'arrow' }[] = [
    { label: 'Pan', value: 'pan' },
    { label: 'Circle', value: 'circle' },
    { label: 'Arrow', value: 'arrow' },
]

watch(viewerViews, (views) => {
    if (!views.length) return
    if (!views.some((view) => view.id === currentViewId.value)) {
        currentViewId.value = views[0].id
    }
}, { immediate: true })


type CircleAnnotationData = CircleViewerAnnotation['data']
type ArrowAnnotationData = ArrowViewerAnnotation['data']


const newThreadForm = reactive({
    guestName: "",
    guestEmail: "",
    content: "",
})

// -----------------------------
// Helper: label threads (1-based index)
// -----------------------------
function threadLabel(threadId: string) {
    const idx = threads.value.findIndex((t) => t.id === threadId)
    return idx >= 0 ? idx + 1 : "?"
}

const replyForm = reactive({
    guestName: "",
    guestEmail: "",
    content: "",
})

const formError = ref<string | null>(null)
const replyError = ref<string | null>(null)

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

function selectTool(tool: 'pan' | 'circle' | 'arrow') {
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
    if (!newThreadForm.guestName.trim() || !newThreadForm.guestEmail.trim()) {
        formError.value = "Guest name and email are required."
        return
    }

    formError.value = null

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
            guest_name: newThreadForm.guestName,
            guest_email: newThreadForm.guestEmail,
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
    if (!replyForm.guestName.trim() || !replyForm.guestEmail.trim()) {
        replyError.value = "Guest name and email are required."
        return
    }

    replyError.value = null

    await addComment(projectId.value, thread.id, {
        content: replyForm.content,
        author_id: null,
        parent_id: null,
        guest_name: replyForm.guestName,
        guest_email: replyForm.guestEmail,
    })

    replyForm.content = ""
    await refreshThreads()
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
</script>

<template>
    <header class="border-b border-border bg-card/80 backdrop-blur">
        <div class="container flex h-16 items-center justify-between">
            <NuxtLink to="/" class="flex items-center gap-2 font-semibold">
                <span class="text-lg">Circuit Scope</span>
            </NuxtLink>


            <div class="flex items-center gap-2">

            </div>
        </div>
    </header>
    <div class="flex h-screen w-full overflow-hidden">

        <!-- Canvas / Viewer area -->
        <div class="relative flex-1 bg-neutral-50 dark:bg-neutral-900">
            <!-- Removed custom view buttons; using viewer's own controls -->
            <!-- View toggle buttons removed -->
            <div class="absolute left-3 top-3 z-20 flex gap-2 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur">
                <button v-for="view in viewerViews" :key="view.id" type="button"
                    class="rounded-md border px-3 py-1 text-xs font-medium"
                    :class="currentViewId === view.id ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-background hover:border-primary/60'"
                    @click="setActiveView(view.id)">{{ view.label }}</button>
            </div>
            <div
                class="absolute left-1/2 top-3 z-20 flex -translate-x-1/2 items-center gap-3 rounded-lg border bg-card/90 px-4 py-2 backdrop-blur">
                <div class="flex items-center gap-1">
                    <button v-for="tool in toolOptions" :key="tool.value" type="button"
                        class="rounded-md px-2 py-1 text-xs font-medium"
                        :class="selectedTool === tool.value ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-muted'"
                        @click="selectTool(tool.value)">
                        {{ tool.label }}
                    </button>
                </div>
                <div class="flex items-center gap-1">
                    <button class="rounded-md border px-2 py-1 text-xs" @click="zoomOut">−</button>
                    <button class="rounded-md border px-2 py-1 text-xs" @click="zoomIn">+</button>
                    <button class="rounded-md border px-2 py-1 text-xs" @click="resetZoom">Reset</button>
                </div>
            </div>

            <!-- Project viewer -->
            <ReviewCanvas ref="viewer" class="h-full w-full" :views="viewerViews"
                :initial-view-id="schematics.length ? 'schematic' : 'pcb-top'" :active-tool="selectedTool"
                :annotations="viewAnnotations" @view-change="setActiveView" @shape-created="handleShapeCreated">
                <!-- existing overlay slot preserved -->
                <template #overlay="slotProps">
                    <component :is="{ ...slotProps }" />
                </template>
            </ReviewCanvas>

            <!-- Sidebar toggle when closed -->
            <button v-if="!sidebarOpen" @click="toggleSidebar"
                class="absolute right-0 top-1/2 z-30 -translate-y-1/2 rounded-l-md border bg-card px-1 py-2 text-xs">&lt;</button>
        </div>

        <!-- Comments sidebar -->
        <aside v-if="sidebarOpen" class="relative w-96 shrink-0 border-l bg-card">
            <button @click="toggleSidebar"
                class="absolute left-0 top-1/2 -translate-x-full -translate-y-1/2 rounded-r-md border bg-card p-2 text-xs">&gt;</button>
            <div class="flex h-full flex-col overflow-hidden p-4">
                <!-- Existing comment panel content pasted here -->
                <!-- START existing sidebar markup -->
                <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between">
                        <h3 class="text-lg font-semibold">New comment</h3>
                        <Button v-if="pendingPin" size="sm" variant="ghost" class="text-muted-foreground"
                            @click="cancelPendingPin">Cancel</Button>
                    </div>
                    <div v-if="formError"
                        class="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                        {{
                            formError }}</div>
                    <p v-if="!pendingPin" class="text-sm text-muted-foreground">Draw a circle or arrow on the canvas to
                        start a
                        new thread.</p>
                    <form v-if="pendingPin" class="space-y-3 overflow-y-auto" @submit.prevent="submitNewThread">
                        <!-- guest fields -->
                        <div class="grid gap-2 text-sm p-2">
                            <label class="flex flex-col gap-1"><span class="font-medium">Guest name</span><Input
                                    v-model="newThreadForm.guestName" placeholder="Jane Reviewer" /></label>
                            <label class="flex flex-col gap-1"><span class="font-medium">Guest email</span><Input
                                    v-model="newThreadForm.guestEmail" type="email"
                                    placeholder="jane@example.com" /></label>
                            <label class="flex flex-col gap-1"><span class="font-medium">Comment</span><Textarea
                                    v-model="newThreadForm.content" rows="3"
                                    placeholder="Share your feedback…" /></label>
                        </div>
                        <div class="flex justify-end gap-2"><Button type="submit" size="sm">Create thread</Button></div>
                    </form>
                </div>

                <!-- Threads list -->
                <div class="mt-4 flex-1 overflow-y-auto rounded-lg border p-4">
                    <div class="mb-3 flex items-center justify-between text-sm text-muted-foreground">
                        <span>{{ threads.length }} thread{{ threads.length === 1 ? '' : 's' }} total</span>
                        <span v-if="threadStatusComputed === 'pending'">Refreshing…</span>
                    </div>
                    <div v-if="threads.length === 0" class="text-sm text-muted-foreground">No comments yet. Draw a shape
                        to start the first thread.</div>
                    <div v-else class="space-y-3">
                        <div v-for="thread in threads" :key="thread.id" class="rounded-md border p-3 text-sm"
                            :class="{ 'border-primary bg-primary/5': thread.id === activeThreadId, 'opacity-60': thread.is_resolved }">
                            <button type="button" class="flex w-full items-center justify-between text-left"
                                @click="openThread(thread)">
                                <div>
                                    <p class="font-medium">Pin #{{ threadLabel(thread.id) }} · {{ thread.view_id }}</p>
                                    <p class="text-xs text-muted-foreground">{{ thread.comment_count }} comment{{
                                        thread.comment_count === 1 ? '' : 's' }}</p>
                                </div>
                                <Badge v-if="thread.is_resolved" variant="secondary">Resolved</Badge>
                            </button>
                            <div v-if="thread.id === activeThreadId" class="mt-3 space-y-3 border-t pt-3">
                                <div v-for="comment in thread.comments" :key="comment.id" class="space-y-1">
                                    <p class="text-xs font-semibold">{{ comment.guest_name ?? 'Guest' }}<span
                                            class="ml-2 text-[11px] text-muted-foreground">{{
                                                formatDateTime(comment.created_at) }}</span></p>
                                    <p class="text-sm leading-relaxed">{{ comment.content }}</p>
                                </div>
                                <div class="flex flex-wrap items-center gap-2"><Button size="sm" variant="outline"
                                        @click="toggleThreadResolution(thread)">{{ thread.is_resolved ? 'Reopen' :
                                            'Mark-as-resolved' }}</Button></div>
                                <div v-if="replyError"
                                    class="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
                                    {{ replyError }}</div>
                                <form class="space-y-2 pt-1" @submit.prevent="submitReply">
                                    <div class="grid gap-2 text-xs">
                                        <label class="flex flex-col gap-1"><span class="font-medium">Name</span><Input
                                                v-model="replyForm.guestName" placeholder="Your name"
                                                size="sm" /></label>
                                        <label class="flex flex-col gap-1"><span class="font-medium">Email</span><Input
                                                v-model="replyForm.guestEmail" placeholder="you@example.com" size="sm"
                                                type="email" /></label>
                                        <label class="flex flex-col gap-1"><span
                                                class="font-medium">Reply</span><Textarea v-model="replyForm.content"
                                                rows="3" placeholder="Write a reply…" /></label>
                                    </div>
                                    <div class="flex justify-end"><Button size="sm" type="submit">Post reply</Button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    </div>
</template>
