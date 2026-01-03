<script setup lang="ts">
import { computed, ref } from 'vue'

import { Button } from '~/components/ui/button'
import type { PreviewAsset } from '~/types/api/projects'

const props = defineProps<{
  photos: PreviewAsset[]
}>()

const activeIndex = ref(0)

const hasPhotos = computed(() => props.photos && props.photos.length > 0)

const activePhoto = computed(() => {
  if (!hasPhotos.value) return null
  const index = Math.min(Math.max(activeIndex.value, 0), props.photos.length - 1)
  return props.photos[index]
})

const zoom = ref(1)
const minZoom = 0.5
const maxZoom = 4
const zoomStep = 0.25
const translate = ref({ x: 0, y: 0 })

const contentRef = ref<HTMLDivElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)

const panOrigin = ref({ x: 0, y: 0 })
const pointerStart = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const activePointerId = ref<number | null>(null)

function goPrevious() {
  if (!hasPhotos.value) return
  activeIndex.value = (activeIndex.value - 1 + props.photos.length) % props.photos.length
  resetView()
}

function goNext() {
  if (!hasPhotos.value) return
  activeIndex.value = (activeIndex.value + 1) % props.photos.length
  resetView()
}

function goTo(index: number) {
  if (!hasPhotos.value) return
  activeIndex.value = index
  resetView()
}

function adjustZoom(direction: 1 | -1) {
  if (!hasPhotos.value || !activePhoto.value) return
  const nextZoom = Number((zoom.value + direction * zoomStep).toFixed(2))
  zoom.value = Math.min(maxZoom, Math.max(minZoom, nextZoom))
}

function resetView() {
  zoom.value = 1
  translate.value = { x: 0, y: 0 }
}

function handleWheel(event: WheelEvent) {
  if (!hasPhotos.value || !activePhoto.value) return
  event.preventDefault()
  const delta = Math.sign(event.deltaY)
  adjustZoom(delta > 0 ? -1 : 1)
}

function handlePointerDown(event: PointerEvent) {
  if (!hasPhotos.value || !activePhoto.value) return
  if (event.pointerType === 'touch') event.preventDefault()
  if (!contentRef.value || isPanning.value) return

  isPanning.value = true
  activePointerId.value = event.pointerId
  pointerStart.value = { x: event.clientX, y: event.clientY }
  panOrigin.value = { ...translate.value }
  contentRef.value.setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (!hasPhotos.value || !activePhoto.value) return
  if (!isPanning.value || activePointerId.value !== event.pointerId) return
  event.preventDefault()

  const deltaX = event.clientX - pointerStart.value.x
  const deltaY = event.clientY - pointerStart.value.y

  translate.value = {
    x: panOrigin.value.x + deltaX,
    y: panOrigin.value.y + deltaY,
  }
}

function handlePointerUp(event: PointerEvent) {
  if (!hasPhotos.value || !activePhoto.value) return
  if (!isPanning.value || activePointerId.value !== event.pointerId) return

  isPanning.value = false
  activePointerId.value = null
  contentRef.value?.releasePointerCapture(event.pointerId)
}

function handlePointerLeave(event: PointerEvent) {
  if (!hasPhotos.value || !activePhoto.value) return
  if (!isPanning.value || activePointerId.value !== event.pointerId) return
  handlePointerUp(event)
}
</script>

<template>
  <div class="w-full">
    <div
      v-if="!hasPhotos"
      class="flex h-64 items-center justify-center rounded-md border border-white/20 bg-cs-charcoal/40 text-sm text-cs-whiteish/80"
    >
      No photos available.
    </div>

    <div
      v-else
      class="space-y-3"
    >
      <div class="flex items-center justify-end gap-2">
        <Button
          size="sm"
          variant="regular"
          class="h-8 w-8 p-0"
          @click="adjustZoom(-1)"
        >
          <span class="text-lg leading-none">−</span>
        </Button>
        <Button
          size="sm"
          variant="regular"
          class="h-8 w-8 p-0"
          @click="adjustZoom(1)"
        >
          <span class="text-lg leading-none">+</span>
        </Button>
        <Button
          size="sm"
          variant="regular"
          class="h-8 px-3"
          @click="resetView()"
        >
          Reset
        </Button>
      </div>

      <div
        ref="contentRef"
        class="relative flex w-full items-center justify-center overflow-hidden rounded-md bg-cs-charcoal py-6 md:py-8 touch-none select-none"
        @wheel.prevent="handleWheel"
        @pointerdown="handlePointerDown"
        @pointermove="handlePointerMove"
        @pointerup="handlePointerUp"
        @pointercancel="handlePointerUp"
        @pointerleave="handlePointerLeave"
      >
        <div
          class="flex items-center justify-center transition-transform duration-75 ease-out"
          :style="{
            transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})`,
          }"
        >
          <img
            v-if="activePhoto?.url"
            ref="imageRef"
            :src="activePhoto.url"
            :alt="activePhoto?.title || activePhoto?.filename || 'Project photo'"
            class="max-h-[60vh] max-w-full object-contain"
            loading="lazy"
          >
          <div
            v-else
            class="text-sm text-cs-whiteish/80"
          >
            Photo not available.
          </div>
        </div>

        <div class="absolute inset-y-0 left-0 flex items-center ml-2">
          <Button
            variant="regular"
            size="icon"
            class="h-8 w-8 rounded-lg"
            @click.stop="goPrevious"
            @pointerdown.stop
          >
            <span class="sr-only">Previous</span>
            <span class="text-lg leading-none">&lt;</span>
          </Button>
        </div>
        <div class="absolute inset-y-0 right-0 flex items-center mr-2">
          <Button
            variant="regular"
            size="icon"
            class="h-8 w-8 rounded-lg"
            @click.stop="goNext"
            @pointerdown.stop
          >
            <span class="sr-only">Next</span>
            <span class="text-lg leading-none">&gt;</span>
          </Button>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-center gap-2">
        <button
          v-for="(photo, index) in props.photos"
          :key="photo.id || index"
          type="button"
          class="h-2 w-2 rounded-full border border-white/50 transition"
          :class="index === activeIndex ? 'bg-white' : 'bg-transparent opacity-60'"
          @click="goTo(index)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.touch-none {
    touch-action: none;
}
</style>
