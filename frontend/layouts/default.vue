<script setup lang="ts">
useBackendUser()
</script>

<template>
  <div class="flex min-h-screen flex-col bg-cs-dark-green text-white">
    <AppHeader />

    <main class="container flex-1">
      <slot />
    </main>

    <footer class="border-t border-white/10 bg-cs-dark-green py-6">
      <div class="container text-sm text-white/60">
        {{ new Date().getFullYear() }} Circuit Scope. All rights reserved.
      </div>
    </footer>
  </div>
</template>
