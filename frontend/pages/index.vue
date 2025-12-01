<script setup lang="ts">
import ProjectsList from "~/components/projects/ProjectsList.vue"

useHead({
  title: "Circuit Scope - Home",
})
</script>

<template>
  <div class="min-h-[calc(100vh-3.5rem)] bg-cs-dark-green">
    <div class="container py-12 px-4 sm:px-8">
      <div class="mb-16 text-center space-y-4">
        <h1 class="text-2xl font-bold text-white font-primary sm:text-3xl md:text-4xl leading-tight">
          Crowdsource design reviews for PCB
          <br class="hidden sm:block" />
          schematics and layouts
        </h1>
        <p class="text-lg italic text-cs-gold font-secondary">
          Made for makers and builders
        </p>
      </div>

      <ProjectsList />
    </div>
  </div>
</template>
