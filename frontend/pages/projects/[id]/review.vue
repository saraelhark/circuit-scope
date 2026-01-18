<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'

import type { ViewerView } from '~/types/viewer'
import ReviewCanvas, {
  type ViewerAnnotation,
  type PinViewerAnnotation,
} from '~/components/projects/ReviewCanvas.vue'
import ReviewCanvasToolbar from '~/components/projects/ReviewCanvasToolbar.vue'
import ReviewCommentsSidebar from '~/components/projects/ReviewCommentsSidebar.vue'
import AppHeader from '~/components/AppHeader.vue'
import { useProject } from '~/composables/useProjects'
import { useCommentThreads } from '~/composables/useCommentThreads'
import { buildReviewViews } from '~/lib/reviewViewer'
import { mapThreadsToAnnotations } from '~/lib/reviewAnnotations'
import type { AnnotationTool, CommentThread, ThreadAnnotation } from '~/types/api/commentThreads'
import type { Project, ProjectPreviewResponse } from '~/types/api/projects'

definePageMeta({
  layout: false,
})

const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.id as string)

const { getProject, getProjectPreviews } = useProject()
const { listThreads, createThread, addComment, updateThreadResolution, deleteThread } = useCommentThreads()

const { status } = useAuth()
const { backendUser } = useBackendUser()

const isAuthenticated = computed(() => status.value === 'authenticated' && !!backendUser.value?.id)

const currentUserInitial = computed(() => {
  if (backendUser.value?.display_name) {
    return backendUser.value.display_name.charAt(0).toUpperCase()
  }
  return '?'
})

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

watch(project, (val) => {
  if (val) {
    defineOgImageComponent('OgTemplate', {
      heading: `Review: ${val.name}`,
      description: val.description || 'Join the community review of this PCB design on Circuit Scope.',
    })
  }
}, { immediate: true })

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
  () => isAuthenticated.value && backendUser.value?.id === projectOwnerId.value,
)

const canDeleteThreads = computed(
  () => isAuthenticated.value && backendUser.value?.id === projectOwnerId.value,
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

const currentUserKey = computed(() => {
  if (isAuthenticated.value && backendUser.value?.id) {
    return backendUser.value.id
  }
  return 'Guest'
})

const authorColorMap = computed(() => {
  const map = new Map<string, string>()
  const palette = ['#FFD02B', '#3B82F6', '#10B981', '#8B5CF6', '#EF4444', '#14B8A6', '#F97316']
  let colorIndex = 0

  const sortedThreads = [...threads.value].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())

  for (const thread of sortedThreads) {
    const comments = thread.comments || []
    for (const comment of comments) {
      const key = comment.author_id || comment.guest_name || 'Anonymous'
      if (!map.has(key)) {
        map.set(key, palette[colorIndex % palette.length])
        colorIndex++
      }
    }
  }

  const myKey = currentUserKey.value
  if (myKey && !map.has(myKey)) {
    map.set(myKey, palette[colorIndex % palette.length])
  }

  return map
})

const currentUserColor = computed(() => {
  return authorColorMap.value.get(currentUserKey.value) || '#FFD02B'
})

const viewAnnotations = computed<Record<string, ViewerAnnotation[]>>(() =>
  mapThreadsToAnnotations(threads.value, authorColorMap.value),
)

const activeThreadId = ref<string | null>(null)
const activeThread = computed(() =>
  threads.value.find(thread => thread.id === activeThreadId.value) ?? null,
)

const highlightedThreadId = ref<string | null>(null)

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

const selectedTool = ref<'pan' | 'pin'>('pan')

type PinCreatedPayload = {
  viewId: string
  pinX: number
  pinY: number
  tool: 'pin'
  data: { initial: string, comment: string, authorName: string }
}

function handlePinCreated(payload: PinCreatedPayload) {
  if (!isAuthenticated.value) {
    router.push('/login')
    return
  }
  pendingPin.value = {
    viewId: payload.viewId,
    x: payload.pinX,
    y: payload.pinY,
    tool: payload.tool,
    data: payload.data,
  }
  activeThreadId.value = null
}

const currentViewId = ref<string>('schematic')
const pendingPin = ref<{
  viewId: string
  x: number
  y: number
  tool: AnnotationTool
  data: PinAnnotationData
} | null>(null)

watch(viewerViews, (views) => {
  if (!views.length) return
  if (!views.some(view => view.id === currentViewId.value)) {
    currentViewId.value = views[0].id
  }
})

type PinAnnotationData = PinViewerAnnotation['data']

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
  pendingPin.value = null
}

function highlightThread(threadId: string) {
  highlightedThreadId.value = threadId
}

function unhighlightThread() {
  highlightedThreadId.value = null
}

function selectTool(tool: 'pan' | 'pin') {
  selectedTool.value = tool
  pendingPin.value = null
}

function cancelPendingPin() {
  pendingPin.value = null
}

async function submitComment(content: string) {
  if (!pendingPin.value) return

  if (!isAuthenticated.value) {
    router.push('/login')
    return
  }

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
      content: content,
    },
  }

  try {
    const created = await createThread(projectId.value, payload)
    pendingPin.value = null
    activeThreadId.value = created.id
    await refreshThreads()
    sidebarOpen.value = true
  }
  catch (e: any) {
    console.error('Failed to create thread', e)
  }
}

async function submitReply(content: string) {
  const thread = activeThread.value
  if (!thread) return

  if (!isAuthenticated.value) {
    router.push('/login')
    return
  }

  try {
    await addComment(projectId.value, thread.id, {
      content: content,
      parent_id: null,
    })
    await refreshThreads()
  }
  catch (e: any) {
    console.error('Failed to submit reply', e)
  }
}

async function toggleThreadResolution(thread: CommentThread) {
  await updateThreadResolution(projectId.value, thread.id, {
    is_resolved: !thread.is_resolved,
    resolved_by_id: null,
  })
  await refreshThreads()
}

async function handleDeleteThread(threadId: string) {
  try {
    await deleteThread(projectId.value, threadId)
    if (activeThreadId.value === threadId) {
      activeThreadId.value = null
    }
    await refreshThreads()
  }
  catch (e: any) {
    console.error('Failed to delete thread', e)
  }
}

const sidebarOpen = ref(true)
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}
const viewer = ref<InstanceType<typeof ReviewCanvas> | null>(null)
function zoomIn() {
  viewer.value?.adjustZoom(1)
}
function zoomOut() {
  viewer.value?.adjustZoom(-1)
}
function resetZoom() {
  viewer.value?.resetView()
}
function flipModel() {
  viewer.value?.flipModel()
}
const isMobile = ref(false)

onMounted(() => {
  if (typeof window !== 'undefined') {
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
  <AppHeader />
  <div class="flex h-screen supports-[height:100dvh]:h-[100dvh] w-full overflow-hidden relative">
    <div class="relative flex-1 bg-neutral-50 dark:bg-neutral-900 w-full h-full">
      <ReviewCanvasToolbar
        :views="viewerViews"
        :current-view-id="currentViewId"
        :selected-tool="selectedTool"
        @select-view="setActiveView"
        @select-tool="selectTool"
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @reset-zoom="resetZoom"
        @flip-view="flipModel"
      />

      <ReviewCanvas
        ref="viewer"
        class="h-full w-full"
        :views="viewerViews"
        :initial-view-id="currentViewId"
        :active-tool="selectedTool"
        :annotations="viewAnnotations"
        :highlighted-thread-id="highlightedThreadId"
        :pending-pin="pendingPin ? { x: pendingPin.x, y: pendingPin.y } : null"
        :active-thread="activeThread"
        :current-user-initial="currentUserInitial"
        :author-color-map="authorColorMap"
        :current-user-color="currentUserColor"
        @view-change="setActiveView"
        @pin-created="handlePinCreated"
        @pin-click="(id) => activeThreadId = id"
        @pin-hover="highlightThread"
        @pin-leave="unhighlightThread"
        @submit-comment="submitComment"
        @cancel-comment="cancelPendingPin"
        @submit-reply="submitReply"
        @resolve-thread="toggleThreadResolution"
        @close-thread="activeThreadId = null"
      >
        <template #overlay="slotProps">
          <component :is="{ ...slotProps }" />
        </template>
      </ReviewCanvas>

      <button
        v-if="!sidebarOpen"
        class="absolute right-0 top-1/2 z-30 -translate-y-1/2 rounded-l-md border bg-card px-1 py-2 text-xs hidden lg:block shadow-md"
        @click="toggleSidebar"
      >
        &lt;
      </button>

      <button
        v-if="!sidebarOpen"
        class="absolute right-4 bottom-4 z-30 rounded-full h-12 w-12 flex items-center justify-center border bg-primary text-primary-foreground shadow-lg lg:hidden"
        @click="toggleSidebar"
      >
        <i class="fas fa-comment-alt text-xl" />
      </button>
    </div>

    <div
      v-if="sidebarOpen && isMobile"
      class="fixed inset-0 bg-black/50 z-40 lg:hidden"
      @click="sidebarOpen = false"
    />

    <aside
      v-if="sidebarOpen"
      class="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-card border-l shadow-xl transition-transform duration-200 lg:relative lg:translate-x-0 lg:shadow-none lg:z-auto shrink-0 flex flex-col"
    >
      <button
        class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-full rounded-l-md border bg-card p-2 text-xs hidden lg:block shadow-md"
        @click="toggleSidebar"
      >
        &gt;
      </button>

      <div class="flex items-center justify-between p-1 border-b lg:hidden">
        <h3 class="font-semibold">
          Comments
        </h3>
        <button
          class="p-2 hover:bg-accent rounded-md"
          @click="toggleSidebar"
        >
          <i class="fas fa-times" />
        </button>
      </div>

      <div class="flex-1 overflow-hidden p-1">
        <ReviewCommentsSidebar
          :threads="threads"
          :active-thread-id="activeThreadId"
          :thread-status="threadStatusComputed"
          :pending-pin-present="false"
          :form-error="null"
          :reply-error="null"
          new-thread-content=""
          reply-content=""
          :can-resolve-threads="canResolveThreads"
          :can-delete-threads="canDeleteThreads"
          @open-thread="openThread"
          @toggle-thread-resolution="toggleThreadResolution"
          @highlight-thread="highlightThread"
          @unhighlight-thread="unhighlightThread"
          @delete-thread="handleDeleteThread"
          @submit-reply="submitReply"
          @thread-selected="(id) => highlightedThreadId = id"
          @thread-deselected="highlightedThreadId = null"
        />
      </div>
    </aside>
  </div>
</template>
