<script setup lang="ts">
import ProjectsList from '~/components/projects/ProjectsList.vue'
import { Button } from '~/components/ui/button'
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
  <div class="min-h-[calc(100vh-3.5rem)] bg-cs-bg">
    <div class="container py-12 px-4 sm:px-8">
      <div class="mb-12 text-center space-y-4">
        <h1 class="text-2xl font-bold text-white font-primary sm:text-3xl md:text-4xl leading-tight">
          Crowdsource design reviews for PCB
          <br class="hidden sm:block">
          schematics and layouts
        </h1>
        <p class="text-lg italic text-cs-copper font-secondary">
          Made for makers and builders
        </p>
        <div class="pt-4">
          <NuxtLink to="/projects/new">
            <Button
              variant="cta"
              class="px-8"
            >
              Upload Your Project
            </Button>
          </NuxtLink>
        </div>
      </div>

      <ProjectsList />
    </div>
  </div>
</template>
