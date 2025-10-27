<script setup lang="ts">
import { Button } from "~/components/ui/button"
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background">
    <header class="border-b border-border bg-card/80 backdrop-blur">
      <div class="container flex h-16 items-center justify-between">
        <NuxtLink to="/" class="flex items-center gap-2 font-semibold">
          <span class="text-lg">Circuit Scope</span>
        </NuxtLink>


        <div class="flex items-center gap-2">

        </div>
      </div>
    </header>

    <main class="container flex-1 py-10">
      <slot />
    </main>

    <footer class="border-t border-border bg-card/80 py-6">
      <div class="container text-sm text-muted-foreground">
        {{ new Date().getFullYear() }} Circuit Scope. All rights reserved.
      </div>
    </footer>
  </div>
</template>
