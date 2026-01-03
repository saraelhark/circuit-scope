<template>
  <div
    class="flex flex-col justify-center items-center bg-[#0F6B45] w-[1200px] h-[630px] p-[80px] overflow-hidden relative"
    style="font-family: sans-serif;"
  >
    <div
      class="absolute inset-0 opacity-20"
      style="background-image: radial-gradient(#1AA36F 1px, transparent 1px); background-size: 40px 40px;"
    />

    <div class="flex flex-col items-center text-center relative">
      <h1 class="text-7xl font-bold text-white mb-[32px] leading-tight">
        {{ heading || 'Circuit Scope' }}
      </h1>

      <p class="text-3xl font-medium text-[#92E3B1] max-w-[900px]">
        {{ description || 'Crowdsource design reviews for PCB schematics and layouts.' }}
      </p>
    </div>

    <div class="absolute bottom-[48px] opacity-60">
      <span class="text-white text-xl">circuitscope.io</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  heading: String,
  description: String,
})

defineOptions({
  name: 'OgTemplate',
})
</script>
