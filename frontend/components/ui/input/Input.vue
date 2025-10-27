<script setup lang="ts">
import type { InputHTMLAttributes } from "vue"
import { cn } from "~/lib/utils"

const props = withDefaults(
  defineProps<{
    modelValue?: string | number | null
    type?: InputHTMLAttributes["type"]
    class?: InputHTMLAttributes["class"]
  }>(),
  {
    type: "text",
  },
)

const emit = defineEmits<{
  (e: "update:modelValue", value: string | number | null): void
}>()

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit("update:modelValue", target.value)
}
</script>

<template>
  <input
    :type="props.type"
    :value="props.modelValue ?? ''"
    :class="cn(
      'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
      props.class,
    )"
    v-bind="$attrs"
    @input="onInput"
  />
</template>
