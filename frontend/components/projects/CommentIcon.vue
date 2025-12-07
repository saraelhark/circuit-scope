<script setup lang="ts">
interface Props {
    initial: string
    size?: "sm" | "md" | "lg"
    color?: string
}

withDefaults(defineProps<Props>(), {
    size: "md",
    color: "#FFD02B"
})
</script>

<template>
    <div class="relative flex items-center justify-center select-none" :class="{
        'w-6 h-6': size === 'sm',
        'w-8 h-8': size === 'md',
        'w-10 h-10': size === 'lg'
    }">

        <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full drop-shadow-md">
            <path d="M0 50A50 50 0 0 1 50 0A50 50 0 0 1 100 50A50 50 0 0 1 50 100L0 100L0 50Z" fill="#1F2937" />

            <circle cx="50" cy="50" r="35" :fill="color" />
        </svg>

        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center font-bold text-cs-charcoal"
            :class="{
                'text-[10px]': size === 'sm',
                'text-sm': size === 'md',
                'text-base': size === 'lg'
            }">
            {{ initial }}
        </div>
    </div>
</template>
