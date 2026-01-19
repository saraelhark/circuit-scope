<script setup lang="ts">
import { Button } from '~/components/ui/button'
import {
  Card,
} from '~/components/ui/card'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { useProjectSubmission } from '~/composables/useProjectSubmission'

definePageMeta({
  layout: 'default',
  middleware: 'auth',
})

useHead({
  title: 'New project – Circuit Scope',
})

defineOgImageComponent('OgTemplate', {
  heading: 'New Project',
  description: 'Upload your KiCad project or board photos for community review.',
})

const {
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
} = useProjectSubmission()

function onTagKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ',' || event.key === ' ' || event.key === 'Tab') {
    event.preventDefault()
    commitCurrentTag()
  }
  else if (event.key === 'Backspace' && form.tagsText === '' && tags.value.length) {
    tags.value.pop()
  }
}

function onImageDragOver(_index: number, event: DragEvent) {
  event.preventDefault()
}

function onImageDragEnd() {
  imageDragIndex.value = null
}
</script>

<template>
  <div class="min-h-screen flex justify-center items-start pt-16">
    <form
      class="w-full max-w-2xl"
      @submit.prevent="handleSubmit"
    >
      <Card class="w-full py-12 px-16">
        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-white font-primary sm:text-2xl md:text-3xl">
            Upload a design for review
          </h1>
        </div>
        <div class="space-y-6">
          <div class="space-y-2">
            <Label
              for="name"
              class="text-white"
            >Project name</Label>
            <Input
              id="name"
              v-model="form.name"
              placeholder="ESP32 IoT weather station"
              required
              class="bg-cs-panel text-white border-cs-border placeholder:text-white/50"
            />
          </div>

          <div class="space-y-2">
            <Label
              for="description"
              class="text-white"
            >Description</Label>
            <Textarea
              id="description"
              v-model="form.description"
              placeholder="Describe the project to give better context for the design review"
              class="bg-cs-panel text-white border-cs-border placeholder:text-white/50"
            />
          </div>

          <div class="space-y-2">
            <Label
              for="tags"
              class="text-white"
            >Tags</Label>
            <div
              class="flex min-h-10 flex-wrap items-center gap-1 rounded-md border border-cs-border bg-cs-panel px-2 py-1 text-sm text-white"
            >
              <Badge
                v-for="(tag, index) in tags"
                :key="`${tag}-${index}`"
                variant="outline"
                class="border-cs-copper bg-cs-bg text-cs-copper text-[11px] px-2 py-0.5 uppercase tracking-wide rounded-sm flex items-center gap-1"
              >
                <span>{{ tag }}</span>
                <button
                  type="button"
                  class="text-[10px] leading-none hover:text-white"
                  @click.stop="removeTag(index)"
                >
                  ×
                </button>
              </Badge>
              <input
                id="tags"
                v-model="form.tagsText"
                type="text"
                placeholder="esp32, battery, sensor"
                class="flex-1 bg-transparent text-white placeholder:text-white/50 outline-none border-none min-w-[80px] py-1"
                @keydown="onTagKeydown"
                @blur="commitCurrentTag"
              >
            </div>
            <p class="text-xs text-white/60">
              Separate tags with commas.
            </p>
          </div>

          <div class="space-y-2">
            <Label class="text-white">Project type</Label>
            <div class="flex gap-4 text-sm text-white/80">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.sourceType"
                  type="radio"
                  value="kicad"
                  class="h-4 w-4"
                >
                <span>KiCad project (ZIP archive)</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.sourceType"
                  type="radio"
                  value="images"
                  class="h-4 w-4"
                >
                <span>Image-only project (PNG/JPEG/WEBP)</span>
              </label>
            </div>
          </div>

          <div
            v-if="form.sourceType === 'kicad'"
            class="space-y-2"
          >
            <Label class="text-white">Thumbnail preview</Label>
            <div class="flex gap-4 text-sm text-white/80">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.thumbnailKind"
                  type="radio"
                  value="pcb"
                  class="h-4 w-4"
                >
                <span>PCB layout</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.thumbnailKind"
                  type="radio"
                  value="schematic"
                  class="h-4 w-4"
                >
                <span>Schematic</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="form.thumbnailKind"
                  type="radio"
                  value="3d"
                  class="h-4 w-4"
                >
                <span>3D model</span>
              </label>
            </div>
          </div>

          <div
            v-if="form.sourceType === 'kicad'"
            class="space-y-2"
          >
            <Label
              for="file"
              class="text-white"
            >Project archive</Label>
            <Input
              id="file"
              type="file"
              accept=".zip"
              class="bg-cs-panel text-white border-cs-border file:text-white file:bg-cs-brand file:border-0 file:mr-3 cursor-pointer"
              @change="onFileChange"
            />
            <p class="text-sm text-white/60">
              Upload a KiCad project archive (max {{ MAX_ARCHIVE_SIZE_MB }} MB).
              Only <code class="text-cs-copper">.zip</code> files are supported.
            </p>
            <p
              v-if="file"
              class="text-xs text-cs-copper"
            >
              Selected file: {{ file?.name }}
            </p>
          </div>

          <div
            v-else
            class="space-y-3"
          >
            <Label
              for="images"
              class="text-white"
            >Project photos</Label>
            <Input
              id="images"
              type="file"
              multiple
              accept="image/png,image/jpeg,image/jpg,image/webp"
              class="bg-cs-panel text-white border-cs-border file:text-white file:bg-cs-brand file:border-0 file:mr-3 cursor-pointer"
              @change="onImagesChange"
            />
            <p class="text-sm text-white/60">
              Upload one or more board photos (each max {{ MAX_IMAGE_SIZE_MB }} MB).
            </p>
            <div
              v-if="imageItems.length"
              class="space-y-2"
            >
              <p class="text-xs text-white/60">
                Drag to reorder. The first image will be used as the main preview.
              </p>
              <div class="flex flex-wrap gap-3">
                <div
                  v-for="(item, index) in imageItems"
                  :key="item.id"
                  class="relative h-20 w-20 flex-shrink-0 cursor-move overflow-hidden rounded-md border border-cs-border bg-cs-panel"
                  draggable="true"
                  :class="imageDragIndex === index ? 'ring-2 ring-cs-lime' : ''"
                  @dragstart="onImageDragStart(index, $event)"
                  @dragover="onImageDragOver(index, $event)"
                  @drop="onImageDrop(index, $event)"
                  @dragend="onImageDragEnd"
                >
                  <img
                    :src="item.previewUrl"
                    :alt="item.file.name"
                    class="h-full w-full object-cover"
                  >
                  <button
                    type="button"
                    class="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-cs-error text-[10px] font-bold text-white shadow"
                    @click.stop="removeImage(item.id)"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="submissionError"
            class="rounded-md border border-cs-red bg-cs-red/20 p-3 text-sm text-white"
          >
            {{ submissionError }}
          </div>
        </div>
        <div class="mt-8 flex items-center justify-end gap-2">
          <Button
            variant="cta"
            type="submit"
            :disabled="submitting"
          >
            <span v-if="submitting">Creating…</span>
            <span v-else>Submit</span>
          </Button>
        </div>
      </Card>
    </form>
  </div>
</template>
