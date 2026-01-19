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
    :class="cn('rounded-lg border border-cs-border bg-cs-card text-white shadow-sm', props.class)"
  >
    <slot />
  </div>
</template>
