<script setup lang="ts">
import { Button } from '~/components/ui/button'

interface Props {
  open: boolean
  alias: string | null
}

defineProps<Props>()

defineEmits<{
  (e: 'continue-anonymous'): void
  (e: 'sign-in'): void
  (e: 'cancel'): void
}>()
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
  >
    <div class="w-full max-w-sm rounded-lg bg-card p-4 shadow-lg">
      <h2 class="mb-2 text-lg font-semibold">
        How do you want to post?
      </h2>
      <p class="mb-4 text-sm text-muted-foreground">
        You can sign in to build your reviewer profile, or continue as an anonymous reviewer.
      </p>
      <div class="space-y-2">
        <Button
          class="w-full"
          size="sm"
          @click="$emit('continue-anonymous')"
        >
          Continue as {{ alias || "anonymous reviewer" }}
        </Button>
        <Button
          class="w-full"
          size="sm"
          variant="outline"
          @click="$emit('sign-in')"
        >
          Sign in
        </Button>
        <Button
          variant="ghost"
          size="sm"
          class="w-full text-xs text-muted-foreground"
          @click="$emit('cancel')"
        >
          Cancel
        </Button>
      </div>
    </div>
  </div>
</template>
