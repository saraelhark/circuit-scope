<script setup lang="ts">
import ProjectsList from '~/components/projects/ProjectsList.vue'
import { useAppSeo } from '~/composables/useAppSeo'

useAppSeo({
  title: 'Circuit Scope',
  description: 'Publish your circuit board design and get reviews from the community, PCB experts, electrical engineers and self-taught makers — works with KiCad.',
  path: '/',
  schemaOrg: {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    'name': 'Circuit Scope',
    'url': 'https://circuitscope.io/',
    'description': 'Publish your circuit board design and get reviews from the community, PCB experts, electrical engineers and self-taught makers — works with KiCad.',
  },
})

defineOgImageComponent('OgTemplate', {
  heading: 'Circuit Scope',
  description: 'Publish your circuit board design and get reviews from the community, PCB experts, electrical engineers and self-taught makers — works with KiCad.',
})
</script>

<template>
  <div class="min-h-[calc(100vh-3.5rem)] bg-cs-dark-green">
    <div class="container py-12 px-4 sm:px-8">
      <div class="mb-16 text-center space-y-4">
        <h1 class="text-2xl font-bold text-white font-primary sm:text-3xl md:text-4xl leading-tight">
          Crowdsource design reviews for PCB
          <br class="hidden sm:block">
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
