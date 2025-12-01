<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { computed } from "vue"
import { cn } from "~/lib/utils"

const props = defineProps<{
  modelValue?: boolean
  disabled?: boolean
  class?: HTMLAttributes["class"]
}>()

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void
}>()

const isChecked = computed({
  get: () => props.modelValue ?? false,
  set: (value: boolean) => emit("update:modelValue", value),
})

function toggle() {
  if (props.disabled) return
  isChecked.value = !isChecked.value
}
</script>

<template>
  <button type="button" role="checkbox" :aria-checked="isChecked" :disabled="props.disabled" :class="cn(
    'flex h-4 w-4 items-center justify-center rounded border border-input bg-background text-primary ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    isChecked ? 'border-primary bg-primary text-primary-foreground' : 'border-input',
    props.class,
  )" @click="toggle">
    <i v-if="isChecked" class="fas fa-check text-[10px] leading-none"></i>
  </button>
</template>
