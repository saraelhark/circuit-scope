<script setup lang="ts">
useBackendUser()
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background">
    <header class="border-b border-border bg-card/80 backdrop-blur">
      <AppHeader />
    </header>

    <main class="container flex-1 py-4">
      <slot />
    </main>

    <footer class="border-t border-border bg-card/80 py-6">
      <div class="container text-sm text-muted-foreground">
        {{ new Date().getFullYear() }} Circuit Scope. All rights reserved.
      </div>
    </footer>
  </div>
</template>
