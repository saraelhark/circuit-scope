<template>
    <div class="container mx-auto p-8 space-y-4">
        <h1 class="text-3xl font-bold mb-6">Circuit Scope</h1>

        <!-- Default Button -->
        <div class="space-x-2">
            <Button>Default Button</Button>
            <Button variant="secondary">Secondary</Button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { Button } from '~/components/ui/button'
</script>
