<script setup lang="ts">
import { ref, nextTick, onMounted } from "vue"
import CommentIcon from "~/components/projects/CommentIcon.vue"

interface Props {
    initial?: string
    x: number
    y: number
    zoom?: number
    color?: string
}

const props = withDefaults(defineProps<Props>(), {
    initial: "G",
    zoom: 1,
    color: "#FFD02B"
})

const emit = defineEmits<{
    (e: "submit", content: string): void
    (e: "cancel"): void
}>()

const content = ref("")
const inputRef = ref<HTMLInputElement | null>(null)

function handleSubmit() {
    if (!content.value.trim()) return
    emit("submit", content.value)
    content.value = ""
}

onMounted(() => {
    nextTick(() => {
        inputRef.value?.focus()
    })
})
</script>

<template>
    <div class="absolute z-[100] flex items-center gap-2" :style="{
        left: `${x * 100}%`,
        top: `${y * 100}%`,
        transform: `translate(0, -100%) scale(${1 / zoom})`,
        transformOrigin: 'bottom left'
    }" @click.stop @mousedown.stop>
        <div class="relative flex flex-col items-center">
            <CommentIcon :initial="initial" size="md" :color="color" />
        </div>

        <div class="flex items-center rounded-[20px] bg-white p-1 pl-4 shadow-xl border border-gray-100 min-w-[280px]">
            <input ref="inputRef" v-model="content" type="text" placeholder="Add a comment"
                class="flex-1 bg-transparent outline-none text-sm text-gray-700 placeholder:text-gray-400 min-w-0"
                @keydown.enter.prevent="handleSubmit" @keydown.esc="emit('cancel')" />
            <button class="ml-2 flex h-8 w-8 items-center justify-center rounded-full transition-colors"
                :class="content.trim() ? 'bg-cs-dark-green text-white hover:opacity-90' : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
                :disabled="!content.trim()" @click="handleSubmit">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 0L4.9425 1.0575L9.1275 5.25H0V6.75H9.1275L4.9425 10.9425L6 12L12 6L6 0Z"
                        fill="currentColor" />
                </svg>
            </button>
        </div>
    </div>
</template>
