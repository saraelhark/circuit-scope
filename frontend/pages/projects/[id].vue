<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Textarea } from "~/components/ui/textarea"
import { formatDateTime } from "~/lib/formatters"
import { normaliseStatus, statusVariant, visibilityLabel } from "~/lib/projects"
import ProjectAssetViewer, { type ViewerView } from "~/components/projects/ProjectAssetViewer.vue"
import type { AnnotationTool, CommentThread, ThreadAnnotation } from "~/types/api/commentThreads"
import type { Project, ProjectPreviewResponse } from "~/types/api/projects"
import { useProject } from "~/composables/useProjects"
import { useCommentThreads } from "~/composables/useCommentThreads"

definePageMeta({
  layout: "default",
})

const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.id as string)

const { getProject, getProjectPreviews } = useProject()
const {
  listThreads,
  createThread,
  addComment,
  updateThreadResolution,
} = useCommentThreads()

const { data, error, refresh, status } = useAsyncData<Project>(
  `project-${projectId.value}`,
  () => getProject(projectId.value),
  {
    watch: [projectId],
  },
)

const project = computed(() => data.value)

const { data: previewData, status: previewStatus } = useAsyncData<ProjectPreviewResponse>(
  `project-${projectId.value}-previews`,
  () => getProjectPreviews(projectId.value),
  {
    watch: [projectId],
  },
)

const previews = computed(() => previewData.value)

const {
  data: threadData,
  status: threadStatus,
  refresh: refreshThreads,
} = useAsyncData(
  `project-${projectId.value}-threads`,
  () => listThreads(projectId.value),
  {
    watch: [projectId],
  },
)

const threads = computed(() => threadData.value?.items ?? [])
const threadStats = computed(() => ({
  total: threadData.value?.total_count ?? 0,
  open: threadData.value?.open_count ?? 0,
  resolved: threadData.value?.resolved_count ?? 0,
}))
const threadStatusComputed = computed(() => threadStatus.value)
const activeThreadId = ref<string | null>(null)

watch(threads, (current) => {
  if (!current.length) {
    activeThreadId.value = null
    return
  }
  if (!current.some((thread) => thread.id === activeThreadId.value)) {
    activeThreadId.value = current[0].id
  }
})

const activeThread = computed(() =>
  threads.value.find((thread) => thread.id === activeThreadId.value) ?? null,
)

type PendingPinPlacement = {
  viewId: string
  x: number
  y: number
  tool: AnnotationTool
  data: Record<string, number>
}

type CircleAnnotationData = { radius: number }
type ArrowAnnotationData = { target_x: number; target_y: number }

const interactionMode = ref<"pan" | "pin">("pan")
const currentViewId = ref<string>("schematic")
const selectedTool = ref<AnnotationTool>("pin")
const placementTool = ref<AnnotationTool>("pin")
const pendingPin = ref<PendingPinPlacement | null>(null)
const pendingArrowTarget = ref<{ x: number; y: number } | null>(null)
const awaitingArrowTarget = ref(false)
const circleRadius = ref(0.08)
const circleRadiusPercent = computed(() => Math.round(circleRadius.value * 100))

const toolOptions: { label: string; value: AnnotationTool }[] = [
  { label: "Pin", value: "pin" },
  { label: "Circle", value: "circle" },
  { label: "Arrow", value: "arrow" },
]

const newThreadForm = reactive({
  guestName: "",
  guestEmail: "",
  content: "",
})

const replyForm = reactive({
  guestName: "",
  guestEmail: "",
  content: "",
})

const formError = ref<string | null>(null)
const replyError = ref<string | null>(null)
const placementMessage = ref<string | null>(null)

const threadsByView = computed<Record<string, CommentThread[]>>(() => {
  return threads.value.reduce((acc, thread) => {
    if (!acc[thread.view_id]) acc[thread.view_id] = []
    acc[thread.view_id].push(thread)
    return acc
  }, {} as Record<string, CommentThread[]>)
})

const overlayItemsByView = computed(
  () =>
    threads.value.reduce(
      (acc, thread) => {
        const bucket = acc[thread.view_id] ?? []
        bucket.push({
          thread,
          circle: asCircleData(thread.annotation),
          arrow: asArrowData(thread.annotation),
        })
        acc[thread.view_id] = bucket
        return acc
      },
      {} as Record<
        string,
        {
          thread: CommentThread
          circle: CircleAnnotationData | null
          arrow: ArrowAnnotationData | null
        }[]
      >,
    ),
)

watch(circleRadius, (value) => {
  if (pendingPin.value?.tool === "circle") {
    pendingPin.value.data.radius = Number(value.toFixed(4))
  }
})

const schematics = computed(() => previews.value?.schematics ?? [])
const layouts = computed(() => previews.value?.layouts ?? [])
const projectMetadata = computed<Record<string, unknown>>(
  () => (previews.value?.project as Record<string, unknown> | undefined) ?? {},
)

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

watch(viewerViews, (views) => {
  if (!views.length) return
  if (!views.some((view) => view.id === currentViewId.value)) {
    currentViewId.value = views[0].id
  }
}, { immediate: true })

const metadataEntries = computed(() =>
  Object.entries(projectMetadata.value).filter(([, value]) => value !== null && value !== undefined && value !== ""),
)

useHead(() => ({
  title: project.value ? `${project.value.name} – Project – Circuit Scope` : "Project – Circuit Scope",
}))

function goBack() {
  router.back()
}

function setActiveView(viewId: string) {
  currentViewId.value = viewId
}

function startPinPlacement() {
  placementTool.value = selectedTool.value
  interactionMode.value = "pin"
  pendingPin.value = null
  pendingArrowTarget.value = null
  awaitingArrowTarget.value = false
  placementMessage.value =
    placementTool.value === "arrow"
      ? "Click once to drop the pin, then click again to choose the arrow direction."
      : "Click on the canvas to drop the pin."
  formError.value = null
}

function cancelPendingPin() {
  interactionMode.value = "pan"
  pendingPin.value = null
  pendingArrowTarget.value = null
  awaitingArrowTarget.value = false
  placementMessage.value = null
  formError.value = null
}

function handleCanvasClick(payload: {
  viewId: string
  relativeX: number
  relativeY: number
}) {
  const x = Number(payload.relativeX.toFixed(5))
  const y = Number(payload.relativeY.toFixed(5))

  if (
    awaitingArrowTarget.value &&
    pendingPin.value &&
    pendingPin.value.tool === "arrow"
  ) {
    if (pendingPin.value.viewId !== payload.viewId) {
      formError.value = "Arrow direction must target the same view as the pin."
      return
    }

    pendingArrowTarget.value = { x, y }
    pendingPin.value.data = {
      target_x: x,
      target_y: y,
    }
    awaitingArrowTarget.value = false
    interactionMode.value = "pan"
    placementMessage.value = "Arrow direction captured. Add your comment below."
    formError.value = null
    return
  }

  if (interactionMode.value !== "pin") return

  pendingPin.value = {
    viewId: payload.viewId,
    x,
    y,
    tool: placementTool.value,
    data:
      placementTool.value === "circle"
        ? { radius: Number(circleRadius.value.toFixed(4)) }
        : {},
  }
  pendingArrowTarget.value = null

  if (placementTool.value === "arrow") {
    awaitingArrowTarget.value = true
    placementMessage.value = "Now click the arrow's end point."
    return
  }

  interactionMode.value = "pan"
  placementMessage.value = "Pin placed. Fill out the form to submit the comment."
}

function threadLabel(threadId: string) {
  const index = threads.value.findIndex((thread) => thread.id === threadId)
  return index >= 0 ? index + 1 : "?"
}

function selectTool(tool: AnnotationTool) {
  selectedTool.value = tool
}

function asCircleData(annotation: ThreadAnnotation | null): CircleAnnotationData | null {
  if (!annotation || annotation.tool !== "circle") return null
  const raw = (annotation.data as Record<string, unknown> | undefined)?.radius
  const radius = typeof raw === "number" ? raw : Number(raw)
  if (!Number.isFinite(radius) || radius <= 0) return null
  return { radius }
}

function asArrowData(annotation: ThreadAnnotation | null): ArrowAnnotationData | null {
  if (!annotation || annotation.tool !== "arrow") return null
  const data = annotation.data as Record<string, unknown> | undefined
  const rawX = data?.target_x
  const rawY = data?.target_y
  const target_x = typeof rawX === "number" ? rawX : Number(rawX)
  const target_y = typeof rawY === "number" ? rawY : Number(rawY)
  if (!Number.isFinite(target_x) || !Number.isFinite(target_y)) return null
  return { target_x, target_y }
}

function clampPercent(value: number) {
  return Math.max(0, Math.min(100, value))
}

function positionStyle(x: number, y: number) {
  return {
    left: `${clampPercent(x * 100)}%`,
    top: `${clampPercent(y * 100)}%`,
  }
}

function circleBoundingStyle(x: number, y: number, radius: number) {
  const diameterPercent = clampPercent(radius * 2 * 100)
  return {
    width: `${diameterPercent}%`,
    height: `${diameterPercent}%`,
    left: `${clampPercent((x - radius) * 100)}%`,
    top: `${clampPercent((y - radius) * 100)}%`,
  }
}

function circleStyle(thread: CommentThread, circle: CircleAnnotationData | null) {
  if (!circle) return null
  return circleBoundingStyle(thread.pin_x, thread.pin_y, circle.radius)
}

function threadStrokeColor(thread: CommentThread) {
  if (thread.id === activeThreadId.value) return "var(--primary)"
  if (thread.is_resolved) return "var(--muted-foreground)"
  return "rgba(251, 191, 36, 0.85)"
}

function threadPinClasses(thread: CommentThread) {
  if (thread.id === activeThreadId.value) return "border-primary bg-primary text-primary-foreground"
  if (thread.is_resolved) return "border-border bg-muted text-muted-foreground"
  return "border-amber-400 bg-amber-100 text-amber-900"
}

function threadPositionStyle(thread: CommentThread) {
  return positionStyle(thread.pin_x, thread.pin_y)
}

const pendingPinStyle = computed(() => {
  if (!pendingPin.value) return null
  return positionStyle(pendingPin.value.x, pendingPin.value.y)
})

const pendingCircleStyle = computed(() => {
  if (!pendingPin.value || pendingPin.value.tool !== "circle") return null
  const radius = pendingPin.value.data.radius ?? circleRadius.value
  return circleBoundingStyle(pendingPin.value.x, pendingPin.value.y, radius)
})

const pendingStrokeColor = "rgba(37, 99, 235, 0.7)"

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

  if (pendingPin.value.tool === "arrow" && !pendingArrowTarget.value) {
    formError.value = "Click a second point to set the arrow direction."
    return
  }

  formError.value = null

  const annotation: ThreadAnnotation | null =
    pendingPin.value.tool === "pin"
      ? null
      : {
          tool: pendingPin.value.tool,
          data: {
            ...(pendingPin.value.data ?? {}),
            ...(pendingPin.value.tool === "circle"
              ? { radius: Number(circleRadius.value.toFixed(4)) }
              : {}),
            ...(pendingPin.value.tool === "arrow" && pendingArrowTarget.value
              ? {
                  target_x: pendingArrowTarget.value.x,
                  target_y: pendingArrowTarget.value.y,
                }
              : {}),
          },
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
  // Keep guest info for future submissions
  pendingPin.value = null
  pendingArrowTarget.value = null
  awaitingArrowTarget.value = false
  placementMessage.value = null
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

const isPlacingPin = computed(() => interactionMode.value === "pin" || pendingPin.value !== null)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="space-y-1">
        <Button variant="ghost" class="-ml-2 text-sm" @click="goBack">
          ← Back
        </Button>
        <h1 class="text-3xl font-semibold tracking-tight">Project details</h1>
        <p class="text-muted-foreground">Review the project's metadata and uploaded files.</p>
      </div>

      <div v-if="project" class="flex items-center gap-2">
        <Badge :variant="statusVariant(project.status)">
          {{ normaliseStatus(project.status) }}
        </Badge>
        <span class="text-sm text-muted-foreground">Updated {{ formatDateTime(project.updated_at) }}</span>
      </div>
    </div>

    <Card v-if="error">
      <CardHeader>
        <CardTitle class="text-xl">Failed to load project</CardTitle>
        <CardDescription>{{ error?.message ?? "Please try again later." }}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="secondary" @click="refresh">
          Retry
        </Button>
      </CardContent>
    </Card>

    <div v-else>
      <div v-if="status === 'pending'" class="flex h-32 items-center justify-center text-muted-foreground">
        Loading project…
      </div>

      <div v-else-if="!project"
        class="rounded-lg border border-dashed border-muted-foreground/30 p-6 text-center text-sm text-muted-foreground">
        Project not found.
      </div>

      <div v-else class="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card class="lg:col-span-2">
          <CardHeader>
            <CardTitle class="text-2xl">{{ project.name }}</CardTitle>
            <CardDescription v-if="project.description" class="max-w-prose">
              {{ project.description }}
            </CardDescription>
          </CardHeader>
          <CardContent class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2">
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Owner:</span>
                {{ project.owner_id }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Visibility:</span>
                {{ visibilityLabel(project) }}
              </p>
            </div>
            <div class="space-y-2">
              <p v-if="project.github_repo_url" class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">GitHub:</span>
                <a class="underline" :href="project.github_repo_url" target="_blank" rel="noopener">
                  {{ project.github_repo_url }}
                </a>
              </p>
              <p v-if="project.secret_link" class="text-sm text-muted-foreground break-all">
                <span class="font-medium text-foreground">Secret link:</span>
                {{ project.secret_link }}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card class="lg:col-span-2">
          <CardHeader>
            <CardTitle>Previews</CardTitle>
            <CardDescription>
              Automatically generated assets from the uploaded KiCad archive.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="previewStatus === 'pending'"
              class="flex h-40 items-center justify-center text-sm text-muted-foreground">
              Generating previews…
            </div>
            <div v-else class="space-y-6">
              <div class="grid gap-6 lg:grid-cols-[3fr_2fr]">
                <ProjectAssetViewer
                  :views="viewerViews"
                  :initial-view-id="schematics.length ? 'schematic' : 'pcb-top'"
                  :interaction-mode="interactionMode"
                  @view-change="setActiveView"
                  @canvas-click="handleCanvasClick"
                >
                  <template #overlay="{ view }">
                    <svg
                      class="pointer-events-none absolute inset-0 h-full w-full"
                      viewBox="0 0 100 100"
                      preserveAspectRatio="none"
                    >
                      <template v-for="item in overlayItemsByView[view.id] ?? []" :key="`${item.thread.id}-arrow`">
                        <template v-if="item.arrow">
                          <line
                            :x1="item.thread.pin_x * 100"
                            :y1="item.thread.pin_y * 100"
                            :x2="item.arrow.target_x * 100"
                            :y2="item.arrow.target_y * 100"
                            :stroke="threadStrokeColor(item.thread)"
                            stroke-width="0.8"
                            stroke-linecap="round"
                          />
                          <circle
                            :cx="item.arrow.target_x * 100"
                            :cy="item.arrow.target_y * 100"
                            r="1.2"
                            :fill="threadStrokeColor(item.thread)"
                          />
                        </template>
                      </template>
                      <template
                        v-if="
                          pendingPin &&
                          pendingPin.viewId === view.id &&
                          pendingPin.tool === 'arrow' &&
                          pendingArrowTarget
                        "
                      >
                        <line
                          :x1="pendingPin.x * 100"
                          :y1="pendingPin.y * 100"
                          :x2="pendingArrowTarget.x * 100"
                          :y2="pendingArrowTarget.y * 100"
                          :stroke="pendingStrokeColor"
                          stroke-dasharray="2 2"
                          stroke-width="0.8"
                          stroke-linecap="round"
                        />
                        <circle
                          :cx="pendingArrowTarget.x * 100"
                          :cy="pendingArrowTarget.y * 100"
                          r="1.2"
                          :fill="pendingStrokeColor"
                        />
                      </template>
                    </svg>

                    <template v-for="item in overlayItemsByView[view.id] ?? []" :key="item.thread.id">
                      <div
                        v-if="circleStyle(item.thread, item.circle)"
                        class="pointer-events-none absolute rounded-full border-2"
                        :class="
                          item.thread.id === activeThreadId
                            ? 'border-primary/80'
                            : item.thread.is_resolved
                              ? 'border-border'
                              : 'border-amber-400/80'
                        "
                        :style="circleStyle(item.thread, item.circle)"
                      />
                      <div
                        class="pointer-events-none absolute flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border text-xs font-semibold transition-colors"
                        :class="threadPinClasses(item.thread)"
                        :style="threadPositionStyle(item.thread)"
                      >
                        {{ threadLabel(item.thread.id) }}
                      </div>
                    </template>

                    <div
                      v-if="pendingPin && pendingPin.viewId === view.id"
                      class="pointer-events-none absolute"
                    >
                      <div
                        v-if="pendingPin.tool === 'circle' && pendingCircleStyle"
                        class="pointer-events-none absolute rounded-full border-2 border-dashed"
                        :style="pendingCircleStyle"
                      />
                      <div
                        class="pointer-events-none absolute flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-dashed bg-primary/10 text-xs font-semibold text-primary"
                        :style="pendingPinStyle"
                      >
                        +
                      </div>
                    </div>
                  </template>
                </ProjectAssetViewer>

                <div class="flex h-full flex-col gap-4">
                  <div class="flex flex-col gap-3">
                    <div class="flex items-center justify-between">
                      <h3 class="text-lg font-semibold">Comments</h3>
                      <div class="flex items-center gap-2">
                        <Button size="sm" variant="outline" @click="startPinPlacement">
                          Drop pin
                        </Button>
                        <Button
                          v-if="pendingPin"
                          size="sm"
                          variant="ghost"
                          class="text-muted-foreground"
                          @click="cancelPendingPin"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>

                    <div class="flex flex-wrap gap-2">
                      <button
                        v-for="tool in toolOptions"
                        :key="tool.value"
                        type="button"
                        class="flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium transition-colors"
                        :class="
                          selectedTool === tool.value
                            ? 'border-primary bg-primary text-primary-foreground'
                            : 'border-border bg-background hover:border-primary/60'
                        "
                        @click="selectTool(tool.value)"
                      >
                        {{ tool.label }}
                      </button>
                    </div>

                    <div
                      v-if="selectedTool === 'circle'"
                      class="flex items-center gap-2 rounded-md border bg-card px-3 py-2 text-xs"
                    >
                      <span class="font-medium text-muted-foreground">Circle radius</span>
                      <input
                        v-model.number="circleRadius"
                        type="range"
                        min="0.02"
                        max="0.25"
                        step="0.01"
                        class="h-2 w-32 rounded-lg bg-muted"
                      />
                      <span class="text-muted-foreground">{{ circleRadiusPercent }}%</span>
                    </div>
                  </div>

                  <p v-if="isPlacingPin" class="rounded-md border border-dashed border-primary/40 bg-primary/5 p-3 text-sm">
                    Click on the canvas to choose where this comment should go.
                  </p>

                  <div v-if="formError" class="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                    {{ formError }}
                  </div>

                  <form v-if="pendingPin" class="space-y-3 rounded-md border bg-card p-3" @submit.prevent="submitNewThread">
                    <p class="text-sm text-muted-foreground">
                      New thread on <span class="font-medium">{{ pendingPin.viewId }}</span>
                    </p>
                    <div class="grid gap-2">
                      <label class="flex flex-col gap-1 text-sm">
                        <span class="font-medium">Guest name</span>
                        <Input v-model="newThreadForm.guestName" placeholder="Jane Reviewer" />
                      </label>
                      <label class="flex flex-col gap-1 text-sm">
                        <span class="font-medium">Guest email</span>
                        <Input v-model="newThreadForm.guestEmail" placeholder="jane@example.com" type="email" />
                      </label>
                      <label class="flex flex-col gap-1 text-sm">
                        <span class="font-medium">Comment</span>
                        <Textarea v-model="newThreadForm.content" rows="3" placeholder="Share your feedback…" />
                      </label>
                    </div>
                    <div class="flex justify-end gap-2">
                      <Button type="submit" size="sm">
                        Create thread
                      </Button>
                    </div>
                  </form>

                  <div class="min-h-[180px] space-y-3 overflow-y-auto pr-1" :class="{ 'opacity-70': threadStatusComputed === 'pending' }">
                    <p v-if="threadStatusComputed === 'pending'" class="text-sm text-muted-foreground">
                      Loading comments…
                    </p>

                    <p v-else-if="threads.length === 0" class="text-sm text-muted-foreground">
                      No comments yet. Drop a pin to start the first thread.
                    </p>

                    <div
                      v-for="thread in threads"
                      :key="thread.id"
                      class="rounded-md border p-3 text-sm"
                      :class="{
                        'border-primary bg-primary/5': thread.id === activeThreadId,
                        'opacity-60': thread.is_resolved,
                      }"
                    >
                      <button
                        type="button"
                        class="flex w-full items-center justify-between text-left"
                        @click="activeThreadId = thread.id"
                      >
                        <div>
                          <p class="font-medium">Pin #{{ threadLabel(thread.id) }} · {{ thread.view_id }}</p>
                          <p class="text-xs text-muted-foreground">
                            {{ thread.comment_count }} comment{{ thread.comment_count === 1 ? '' : 's' }}
                          </p>
                        </div>
                        <Badge v-if="thread.is_resolved" variant="secondary">Resolved</Badge>
                      </button>

                      <div v-if="thread.id === activeThreadId" class="mt-3 space-y-3 border-t pt-3">
                        <div v-for="comment in thread.comments" :key="comment.id" class="space-y-1">
                          <p class="text-xs font-semibold">
                            {{ comment.guest_name ?? 'Guest' }}
                            <span class="ml-2 text-[11px] text-muted-foreground">{{ formatDateTime(comment.created_at) }}</span>
                          </p>
                          <p class="text-sm leading-relaxed">{{ comment.content }}</p>
                        </div>

                        <div class="flex flex-wrap items-center gap-2">
                          <Button size="sm" variant="outline" @click="toggleThreadResolution(thread)">
                            {{ thread.is_resolved ? 'Reopen' : 'Mark as resolved' }}
                          </Button>
                        </div>

                        <div v-if="replyError" class="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
                          {{ replyError }}
                        </div>

                        <form class="space-y-2 pt-1" @submit.prevent="submitReply">
                          <div class="grid gap-2 text-xs">
                            <label class="flex flex-col gap-1">
                              <span class="font-medium">Name</span>
                              <Input v-model="replyForm.guestName" placeholder="Your name" size="sm" />
                            </label>
                            <label class="flex flex-col gap-1">
                              <span class="font-medium">Email</span>
                              <Input v-model="replyForm.guestEmail" placeholder="you@example.com" size="sm" type="email" />
                            </label>
                            <label class="flex flex-col gap-1">
                              <span class="font-medium">Reply</span>
                              <Textarea v-model="replyForm.content" rows="3" placeholder="Write a reply…" />
                            </label>
                          </div>
                          <div class="flex justify-end">
                            <Button size="sm" type="submit">
                              Post reply
                            </Button>
                          </div>
                        </form>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
