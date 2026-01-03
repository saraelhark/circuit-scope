<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { useAttrs } from 'vue'
import { cn } from '~/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()

const attrs = useAttrs()
</script>

<template>
  <div
    v-bind="attrs"
    :class="cn('rounded-[8px] border-4 border-white bg-cs-light-green text-white shadow-sm', props.class)"
  >
    <slot />
  </div>
</template>
