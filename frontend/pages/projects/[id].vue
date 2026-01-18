<script setup lang="ts">
// This page redirects to the review page for backwards compatibility
// with old bookmarked links to /projects/[id]
const route = useRoute()
const projectId = computed(() => route.params.id as string)

// Redirect to review page
await navigateTo(`/projects/${projectId.value}/review`, { replace: true })
</script>

<template>
  <div class="min-h-screen flex items-center justify-center">
    <div class="text-muted-foreground">
      Redirecting...
    </div>
  </div>
</template>
