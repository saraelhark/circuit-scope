<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTimeAgo, onClickOutside } from '@vueuse/core'
import { Button } from '~/components/ui/button'
import { Card } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { formatDateTime } from '~/lib/formatters'
import { normaliseStatus, statusVariant } from '~/lib/projects'
import type { Project } from '~/types/api/projects'
import ProjectPreviewThumbnail from '~/components/projects/ProjectPreviewThumbnail.vue'
import ProjectStats from '~/components/projects/ProjectStats.vue'

const props = defineProps<{
  project: Project
}>()

const emit = defineEmits<{
  (e: 'update-status', id: string, status: string): void
  (e: 'update-metadata', id: string, payload: { name?: string | null, description?: string | null }): void
}>()

const timeAgo = useTimeAgo(() => new Date(props.project.updated_at))
const isArchived = computed(() => props.project.status === 'closed')

const isEditing = ref(false)
const editName = ref(props.project.name)
const editDescription = ref(props.project.description ?? '')
const showStatusMenu = ref(false)
const statusMenuRef = ref<HTMLElement | null>(null)

onClickOutside(statusMenuRef, () => {
  showStatusMenu.value = false
})

const router = useRouter()

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

function goToProject() {
  if (isEditing.value) return
  router.push(`/projects/${props.project.id}/review`)
}

async function shareProject() {
  if (!import.meta.client) return

  try {
    const origin = window.location.origin
    const url = `${origin}/projects/${props.project.id}`

    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(url)
    }
    else {
      console.warn('Clipboard API not available. Could not copy project link automatically.', url)
    }
  }
  catch (error) {
    console.error('Failed to copy project link', error)
  }
}
</script>

<template>
  <Card class="flex flex-col gap-4 p-4 transition-all sm:flex-row sm:items-center sm:justify-between">
    <div class="flex flex-1 items-start gap-4">
      <div class="h-16 w-16 shrink-0">
        <ProjectPreviewThumbnail
          :project-id="project.id"
          :thumbnail-kind="project.thumbnail_kind"
          :source-type="project.source_type"
        />
      </div>

      <div class="flex flex-col gap-1">
        <div class="flex items-center gap-2">
          <template v-if="isEditing">
            <Input
              :id="`project-${project.id}-name-inline`"
              v-model="editName"
              class="h-8 px-2 py-1 text-sm font-semibold text-white bg-cs-charcoal/40 border-white/60"
            />
          </template>
          <h3
            v-else
            class="font-semibold leading-none tracking-tight text-white font-primary"
          >
            {{ project.name }}
          </h3>
          <div
            ref="statusMenuRef"
            class="relative flex items-center gap-2"
          >
            <Badge
              :variant="statusVariant(project.status)"
              class="h-5 px-2 capitalize"
            >
              {{ normaliseStatus(project.status) }}
            </Badge>
            <button
              type="button"
              class="inline-flex items-center justify-center ml-2 rounded-md border border-white text-white hover:bg-white/10 h-6 w-6 text-[10px]"
              @click.stop="showStatusMenu = !showStatusMenu"
            >
              <i class="fas fa-ellipsis-v h-3 w-3" />
            </button>

            <div
              v-if="showStatusMenu"
              class="absolute right-0 z-10 mt-12 p-1 w-40 rounded-lg border border-white/30 bg-cs-light-green text-xs text-foreground"
              @click.stop
            >
              <button
                type="button"
                class="flex w-full items-center gap-2 p-2 rounded-sm hover:bg-cs-charcoal/10"
                @click.stop="startEdit(); showStatusMenu = false"
              >
                <i class="fas fa-pencil-alt h-4 w-4" />
                <span>Edit project</span>
              </button>
              <button
                type="button"
                class="flex w-full items-center gap-2 p-2 rounded-sm hover:bg-cs-charcoal/10"
                @click.stop="toggleStatus(); showStatusMenu = false"
              >
                <i :class="isArchived ? 'fas fa-rotate h-4 w-4' : 'fas fa-archive h-4 w-4'" />
                <span>{{ isArchived ? 'Re-open project' : 'Archive project' }}</span>
              </button>
            </div>
          </div>
        </div>

        <div
          class="flex flex-col gap-1 text-xs text-white/80 sm:flex-row sm:items-center sm:gap-4 font-secondary"
        >
          <div class="flex items-center gap-1">
            <i class="far fa-calendar h-3.5 w-3.5" />
            <span>Posted on {{ formatDateTime(project.created_at, undefined, {
              dateStyle: 'medium',
              timeStyle: undefined,
            }) }}</span>
          </div>
          <div class="hidden sm:block">
            •
          </div>
          <div class="flex items-center gap-1">
            <i class="far fa-clock h-3.5 w-3.5" />
            <span>Active {{ timeAgo }}</span>
          </div>
        </div>

        <div class="mt-1">
          <ProjectStats
            :comment-count="project.total_comment_count"
            :view-count="project.view_count"
          />
        </div>

        <div
          v-if="isEditing"
          class="mt-3 flex flex-col gap-3 max-w-md"
          @click.stop
        >
          <div class="space-y-1">
            <Label :for="`project-${project.id}-description`">Description</Label>
            <Textarea
              :id="`project-${project.id}-description`"
              v-model="editDescription"
              rows="3"
            />
          </div>
          <div class="flex items-center gap-2">
            <Button
              size="sm"
              variant="regular"
              class="h-8 px-3"
              @click="saveEdit"
            >
              Save
            </Button>
            <Button
              variant="ghost"
              size="sm"
              class="h-8 px-3"
              @click="cancelEdit"
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2 sm:self-center">
      <Button
        variant="regular"
        size="icon"
        class="h-9 w-9"
        @click.stop="goToProject"
      >
        <i class="fas fa-external-link-alt h-4 w-4" />
        <span class="sr-only">Open project</span>
      </Button>

      <Button
        variant="regular"
        size="icon"
        class="h-9 w-9"
        @click.stop="shareProject"
      >
        <i class="fas fa-share-alt h-4 w-4" />
        <span class="sr-only">Share project</span>
      </Button>
    </div>
  </Card>
</template>
