<script setup lang="ts">
import { reactive, ref, computed, onUnmounted } from "vue"

import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
} from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Badge } from "~/components/ui/badge"
import { Label } from "~/components/ui/label"
import { Textarea } from "~/components/ui/textarea"
import { useProject } from "~/composables/useProjects"
import type { ProjectCreatePayload } from "~/types/api/projects"

definePageMeta({
  layout: "default",
  middleware: "auth",
})

useHead({
  title: "New project – Circuit Scope",
})

const router = useRouter()
const { createProject } = useProject()
const { backendUser } = useBackendUser()

const MAX_ARCHIVE_SIZE_MB = 30
const MAX_ARCHIVE_SIZE_BYTES = MAX_ARCHIVE_SIZE_MB * 1024 * 1024
const MAX_IMAGE_SIZE_MB = 15
const MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

const form = reactive({
  name: "",
  description: "",
  tagsText: "",
  sourceType: "kicad" as "kicad" | "images",
  thumbnailKind: "pcb" as "pcb" | "schematic" | "3d",
})

const file = ref<File | null>(null)
type ImageItem = {
  id: number
  file: File
  previewUrl: string
}

const imageItems = ref<ImageItem[]>([])
const imageDragIndex = ref<number | null>(null)
let nextImageId = 0

const imageFiles = computed(() => imageItems.value.map((item) => item.file))
const submitting = ref(false)
const submissionError = ref<string | null>(null)
const tags = ref<string[]>([])

function normaliseTagValue(raw: string): string | null {
  const cleaned = raw.replace(/[,]+/g, " ").trim()
  return cleaned || null
}

function commitCurrentTag() {
  const value = normaliseTagValue(form.tagsText)
  if (!value) {
    form.tagsText = ""
    return
  }

  if (!tags.value.includes(value)) {
    tags.value.push(value)
  }

  // Clear the input so the committed tag only appears as a chip.
  form.tagsText = ""
}

function onTagKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" || event.key === "," || event.key === " " || event.key === "Tab") {
    event.preventDefault()
    commitCurrentTag()
  } else if (event.key === "Backspace" && form.tagsText === "" && tags.value.length) {
    // Allow quickly deleting the last tag with backspace when the input is empty.
    tags.value.pop()
  }
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

  const tooLarge = files.find((f) => f.size > MAX_IMAGE_SIZE_BYTES)
  if (tooLarge) {
    clearImageItems()
    submissionError.value = `Each image must be ${MAX_IMAGE_SIZE_MB} MB or smaller.`
    return
  }

  clearImageItems()

  imageItems.value = files.map((file) => ({
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
  const index = imageItems.value.findIndex((item) => item.id === id)
  if (index === -1) return

  URL.revokeObjectURL(imageItems.value[index].previewUrl)
  imageItems.value.splice(index, 1)
}

function onImageDragStart(index: number, event: DragEvent) {
  imageDragIndex.value = index
  event.dataTransfer?.setData("text/plain", String(index))
}

function onImageDragOver(_index: number, event: DragEvent) {
  event.preventDefault()
}

function onImageDrop(index: number, event: DragEvent) {
  event.preventDefault()

  const fromData = event.dataTransfer?.getData("text/plain")
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

function onImageDragEnd() {
  imageDragIndex.value = null
}

onUnmounted(() => {
  clearImageItems()
})

async function handleSubmit() {
  submitting.value = true
  submissionError.value = null

  if (!form.name) {
    submissionError.value = "Project name is required."
    submitting.value = false
    return
  }

  if (!backendUser.value || !backendUser.value.id) {
    submissionError.value = "You must be signed in to create a project."
    submitting.value = false
    return
  }

  try {
    // Ensure any in-progress tag is committed before submission.
    commitCurrentTag()
    const rawTags = tags.value

    const thumbnailKind =
      form.sourceType === "images"
        ? "photo"
        : form.thumbnailKind

    const payload: ProjectCreatePayload = {
      name: form.name,
      description: form.description || undefined,
      owner_id: backendUser.value.id,
      tags: rawTags.length ? rawTags : undefined,
      source_type: form.sourceType,
      thumbnail_kind: thumbnailKind,
    }

    if (form.sourceType === "images" && imageFiles.value.length === 0) {
      submissionError.value = "Please upload at least one image for an image-only project."
      submitting.value = false
      return
    }

    const response = await createProject(
      payload,
      form.sourceType === "kicad" ? file.value ?? undefined : undefined,
      form.sourceType === "images" ? imageFiles.value : undefined,
    )
    router.push(`/projects/${response.project.id}`)
  } catch (error: any) {
    submissionError.value = error?.data?.detail ?? error?.message ?? "Failed to create project."
  } finally {
    submitting.value = false
  }
}

</script>

<template>
  <div class="min-h-screen flex justify-center items-start pt-16">
    <form class="w-full max-w-2xl" @submit.prevent="handleSubmit">
      <Card class="w-full py-12 px-16">
        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-white font-primary sm:text-2xl md:text-3xl">Upload a design for review</h1>
        </div>
        <div class="space-y-6">
          <div class="space-y-2">
            <Label for="name" class="text-white">Project name</Label>
            <Input id="name" v-model="form.name" placeholder="ESP32 IoT weather station" required
              class="bg-white text-cs-charcoal border-cs-whiteish" />
          </div>

          <div class="space-y-2">
            <Label for="description" class="text-white">Description</Label>
            <Textarea id="description" v-model="form.description"
              placeholder="Describe the project to give better context for the design review"
              class="bg-white text-cs-charcoal border-cs-whiteish" />
          </div>

          <div class="space-y-2">
            <Label for="tags" class="text-white">Tags</Label>
            <div
              class="flex min-h-10 flex-wrap items-center gap-1 rounded-md border border-cs-whiteish bg-white px-2 py-1 text-sm text-cs-charcoal">
              <Badge v-for="(tag, index) in tags" :key="`${tag}-${index}`" variant="outline"
                class="border-cs-gold bg-cs-blue/80 text-cs-whiteish text-[11px] px-2 py-0.5 uppercase tracking-wide rounded-sm flex items-center gap-1">
                <span>{{ tag }}</span>
                <button type="button" class="text-[10px] leading-none" @click.stop="removeTag(index)">
                  ×
                </button>
              </Badge>
              <input id="tags" v-model="form.tagsText" type="text" placeholder="esp32, battery, sensor"
                class="flex-1 bg-transparent text-cs-charcoal placeholder:text-cs-charcoal/60 outline-none border-none min-w-[80px] py-1"
                @keydown="onTagKeydown" @blur="commitCurrentTag" />
            </div>
            <p class="text-xs text-cs-whiteish/80">
              Separate tags with commas.
            </p>
          </div>

          <div class="space-y-2">
            <Label class="text-white">Project type</Label>
            <div class="flex gap-4 text-sm text-cs-whiteish/90">
              <label class="flex items-center gap-2 cursor-pointer">
                <input v-model="form.sourceType" type="radio" value="kicad" class="h-4 w-4" />
                <span>KiCad project (ZIP archive)</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input v-model="form.sourceType" type="radio" value="images" class="h-4 w-4" />
                <span>Image-only project (PNG/JPEG/WEBP)</span>
              </label>
            </div>
          </div>

          <div v-if="form.sourceType === 'kicad'" class="space-y-2">
            <Label class="text-white">Thumbnail preview</Label>
            <div class="flex gap-4 text-sm text-cs-whiteish/90">
              <label class="flex items-center gap-2 cursor-pointer">
                <input v-model="form.thumbnailKind" type="radio" value="pcb" class="h-4 w-4" />
                <span>PCB layout</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input v-model="form.thumbnailKind" type="radio" value="schematic" class="h-4 w-4" />
                <span>Schematic</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input v-model="form.thumbnailKind" type="radio" value="3d" class="h-4 w-4" />
                <span>3D model</span>
              </label>
            </div>
          </div>

          <div v-if="form.sourceType === 'kicad'" class="space-y-2">
            <Label for="file" class="text-white">Project archive</Label>
            <Input id="file" type="file" accept=".zip" @change="onFileChange"
              class="bg-white text-cs-charcoal border-cs-whiteish file:text-cs-charcoal cursor-pointer" />
            <p class="text-sm text-cs-whiteish/80">
              Upload a KiCad project archive (max {{ MAX_ARCHIVE_SIZE_MB }} MB).
              Only <code>.zip</code> files are supported.
            </p>
            <p v-if="file" class="text-xs text-cs-whiteish/80">
              Selected file: {{ file?.name }}
            </p>
          </div>

          <div v-else class="space-y-3">
            <Label for="images" class="text-white">Project photos</Label>
            <Input id="images" type="file" multiple accept="image/png,image/jpeg,image/jpg,image/webp"
              @change="onImagesChange"
              class="bg-white text-cs-charcoal border-cs-whiteish file:text-cs-charcoal cursor-pointer" />
            <p class="text-sm text-cs-whiteish/80">
              Upload one or more board photos (each max {{ MAX_IMAGE_SIZE_MB }} MB).
            </p>
            <div v-if="imageItems.length" class="space-y-2">
              <p class="text-xs text-cs-whiteish/80">
                Drag to reorder. The first image will be used as the main preview.
              </p>
              <div class="flex flex-wrap gap-3">
                <div v-for="(item, index) in imageItems" :key="item.id"
                  class="relative h-20 w-20 flex-shrink-0 cursor-move overflow-hidden rounded-md border border-cs-whiteish/70 bg-cs-charcoal/80"
                  draggable="true" @dragstart="onImageDragStart(index, $event)"
                  @dragover="onImageDragOver(index, $event)" @drop="onImageDrop(index, $event)"
                  @dragend="onImageDragEnd" :class="imageDragIndex === index ? 'ring-2 ring-cs-lime' : ''">
                  <img :src="item.previewUrl" :alt="item.file.name" class="h-full w-full object-cover" />
                  <button type="button"
                    class="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-cs-red text-[10px] font-bold text-white shadow"
                    @click.stop="removeImage(item.id)">
                    ×
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="submissionError" class="rounded-md border border-cs-red bg-cs-red/20 p-3 text-sm text-white">
            {{ submissionError }}
          </div>
        </div>
        <div class="mt-8 flex items-center justify-end gap-2">
          <Button variant="cta" type="submit" :disabled="submitting">
            <span v-if="submitting">Creating…</span>
            <span v-else>Submit</span>
          </Button>
        </div>
      </Card>
    </form>
  </div>
</template>
