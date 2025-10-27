<template>
  <div class="min-h-screen bg-background text-foreground">
    <NuxtLoadingIndicator color="hsl(var(--primary))" />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <NuxtRouteAnnouncer />
  </div>
</template>
