<script setup lang="ts">
useBackendUser()
</script>

<template>
  <div class="flex min-h-screen flex-col bg-cs-bg text-white">
    <AppHeader />

    <main class="container flex-1">
      <slot />
    </main>

    <footer class="border-t border-cs-border bg-cs-panel py-6">
      <div class="container flex items-center justify-between text-sm text-white/60">
        <div>
          {{ new Date().getFullYear() }} Circuit Scope. All rights reserved.
        </div>
        <div class="flex flex-col items-end gap-1">
          <NuxtLink
            to="/privacy"
            class="hover:text-white"
          >Privacy Policy</NuxtLink>
          <NuxtLink
            to="/tos"
            class="hover:text-white"
          >Terms of Service</NuxtLink>
        </div>
      </div>
    </footer>
  </div>
</template>
