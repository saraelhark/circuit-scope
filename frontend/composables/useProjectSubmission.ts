import { reactive, ref, computed, onUnmounted } from 'vue'
import { useProject } from '~/composables/useProjects'
import type { ProjectCreatePayload } from '~/types/api/projects'

const MAX_ARCHIVE_SIZE_MB = 30
const MAX_ARCHIVE_SIZE_BYTES = MAX_ARCHIVE_SIZE_MB * 1024 * 1024
const MAX_IMAGE_SIZE_MB = 15
const MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

type ImageItem = {
  id: number
  file: File
  previewUrl: string
}

export function useProjectSubmission() {
  const { createProject } = useProject()
  const { backendUser } = useBackendUser()
  const router = useRouter()

  const form = reactive({
    name: '',
    description: '',
    tagsText: '',
    sourceType: 'kicad' as 'kicad' | 'images',
    thumbnailKind: 'pcb' as 'pcb' | 'schematic' | '3d',
  })

  const file = ref<File | null>(null)
  const imageItems = ref<ImageItem[]>([])
  const imageDragIndex = ref<number | null>(null)
  const tags = ref<string[]>([])
  const submitting = ref(false)
  const submissionError = ref<string | null>(null)

  let nextImageId = 0

  const imageFiles = computed(() => imageItems.value.map(item => item.file))

  function normaliseTagValue(raw: string): string | null {
    const cleaned = raw.replace(/[,]+/g, ' ').trim()
    return cleaned || null
  }

  function commitCurrentTag() {
    const value = normaliseTagValue(form.tagsText)
    if (!value) {
      form.tagsText = ''
      return
    }
    if (!tags.value.includes(value)) {
      tags.value.push(value)
    }
    form.tagsText = ''
  }

  function removeTag(index: number) {
    tags.value.splice(index, 1)
  }

  function onFileChange(event: Event) {
    const target = event.target as HTMLInputElement
    const selected = target.files?.[0] ?? null
    submissionError.value = null

    if (selected && selected.size > MAX_ARCHIVE_SIZE_BYTES) {
      file.value = null
      submissionError.value = `KiCad archive must be ${MAX_ARCHIVE_SIZE_MB} MB or smaller.`
      return
    }
    file.value = selected
  }

  function onImagesChange(event: Event) {
    const target = event.target as HTMLInputElement
    const files = Array.from(target.files ?? [])
    submissionError.value = null

    if (!files.length) {
      clearImageItems()
      return
    }

    const tooLarge = files.find(f => f.size > MAX_IMAGE_SIZE_BYTES)
    if (tooLarge) {
      clearImageItems()
      submissionError.value = `Each image must be ${MAX_IMAGE_SIZE_MB} MB or smaller.`
      return
    }

    clearImageItems()
    imageItems.value = files.map(file => ({
      id: nextImageId++,
      file,
      previewUrl: URL.createObjectURL(file),
    }))
  }

  function clearImageItems() {
    for (const item of imageItems.value) {
      URL.revokeObjectURL(item.previewUrl)
    }
    imageItems.value = []
  }

  function removeImage(id: number) {
    const index = imageItems.value.findIndex(item => item.id === id)
    if (index === -1) return
    URL.revokeObjectURL(imageItems.value[index].previewUrl)
    imageItems.value.splice(index, 1)
  }

  function onImageDragStart(index: number, event: DragEvent) {
    imageDragIndex.value = index
    event.dataTransfer?.setData('text/plain', String(index))
  }

  function onImageDrop(index: number, event: DragEvent) {
    event.preventDefault()
    const fromData = event.dataTransfer?.getData('text/plain')
    const fromIndex = imageDragIndex.value ?? (fromData ? Number(fromData) : -1)

    if (fromIndex === -1 || fromIndex === index) {
      imageDragIndex.value = null
      return
    }

    if (fromIndex < 0 || fromIndex >= imageItems.value.length || index < 0 || index >= imageItems.value.length) {
      imageDragIndex.value = null
      return
    }

    const updated = [...imageItems.value]
    const [moved] = updated.splice(fromIndex, 1)
    updated.splice(index, 0, moved)
    imageItems.value = updated
    imageDragIndex.value = null
  }

  async function handleSubmit() {
    submitting.value = true
    submissionError.value = null

    if (!form.name) {
      submissionError.value = 'Project name is required.'
      submitting.value = false
      return
    }

    if (!backendUser.value || !backendUser.value.id) {
      submissionError.value = 'You must be signed in to create a project.'
      submitting.value = false
      return
    }

    try {
      commitCurrentTag()
      const rawTags = tags.value
      const thumbnailKind = form.sourceType === 'images' ? 'photo' : form.thumbnailKind

      const payload: ProjectCreatePayload = {
        name: form.name,
        description: form.description || undefined,
        owner_id: backendUser.value.id,
        tags: rawTags.length ? rawTags : undefined,
        source_type: form.sourceType,
        thumbnail_kind: thumbnailKind,
      }

      if (form.sourceType === 'images' && imageFiles.value.length === 0) {
        submissionError.value = 'Please upload at least one image for an image-only project.'
        submitting.value = false
        return
      }

      const response = await createProject(
        payload,
        form.sourceType === 'kicad' ? file.value ?? undefined : undefined,
        form.sourceType === 'images' ? imageFiles.value : undefined,
      )
      router.push(`/projects/${response.project.id}/review`)
    }
    catch (error: any) {
      submissionError.value = error?.data?.detail ?? error?.message ?? 'Failed to create project.'
    }
    finally {
      submitting.value = false
    }
  }

  onUnmounted(() => {
    clearImageItems()
  })

  return {
    form,
    file,
    imageItems,
    imageDragIndex,
    submitting,
    submissionError,
    tags,
    MAX_ARCHIVE_SIZE_MB,
    MAX_IMAGE_SIZE_MB,
    commitCurrentTag,
    removeTag,
    onFileChange,
    onImagesChange,
    removeImage,
    onImageDragStart,
    onImageDrop,
    handleSubmit,
  }
}
