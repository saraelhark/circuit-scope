<template>
    <header
        class="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div class="container flex h-14 items-center justify-between">
            <div class="flex items-center gap-4">
                <NuxtLink to="/" class="flex items-center gap-2 text-xl font-bold text-foreground">
                    <div class="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="h-5 w-5 text-primary">
                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                        </svg>
                    </div>
                    Circuit Scope
                </NuxtLink>
            </div>

            <div class="flex items-center gap-4">
                <template v-if="isSignedIn">
                    <NuxtLink to="/projects/new">
                        <Button size="sm">Upload Project</Button>
                    </NuxtLink>

                    <div class="relative">
                        <Button variant="ghost" size="icon" class="relative">
                            <Bell class="h-5 w-5" />
                            <span class="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 opacity-0"></span>
                        </Button>
                    </div>

                    <div class="relative ml-2" ref="userMenuRef">
                        <button @click="toggleUserMenu" class="flex items-center gap-2 outline-none">
                            <div
                                class="h-8 w-8 rounded-full bg-secondary flex items-center justify-center overflow-hidden border text-muted-foreground">
                                <img v-if="user?.image" :src="user.image" :alt="user.name || 'User'"
                                    class="h-full w-full object-cover" />
                                <User v-else class="h-4 w-4" />
                            </div>
                        </button>

                        <div v-if="isUserMenuOpen"
                            class="absolute right-0 mt-2 w-56 origin-top-right rounded-md border bg-popover p-1 shadow-md focus:outline-none animate-in fade-in zoom-in-95 duration-200">
                            <div class="px-2 py-1.5 text-sm font-semibold">
                                {{ user?.name || user?.email }}
                            </div>
                            <div class="h-px my-1 bg-muted"></div>
                            <NuxtLink to="/dashboard"
                                class="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                                @click="isUserMenuOpen = false">
                                <Folder class="mr-2 h-4 w-4" />
                                <span>My Projects</span>
                            </NuxtLink>
                            <div class="h-px my-1 bg-muted"></div>
                            <button @click="handleSignOut"
                                class="relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground text-red-500">
                                <LogOut class="mr-2 h-4 w-4" />
                                <span>Sign out</span>
                            </button>
                        </div>
                    </div>
                </template>

                <template v-else>
                    <NuxtLink to="/login">
                        <Button size="sm">Log in</Button>
                    </NuxtLink>
                </template>
            </div>
        </div>
    </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Bell, User, LogOut, Folder } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { onClickOutside } from '@vueuse/core'

const { data: session, status, signOut } = useAuth()
const user = computed(() => session.value?.user)
const isSignedIn = computed(() => status.value === 'authenticated')

const isUserMenuOpen = ref(false)
const userMenuRef = ref(null)

function toggleUserMenu() {
    isUserMenuOpen.value = !isUserMenuOpen.value
}

onClickOutside(userMenuRef, () => {
    isUserMenuOpen.value = false
})

const handleSignOut = async () => {
    try {
        await signOut()
        isUserMenuOpen.value = false
        await navigateTo('/')
    } catch (error) {
        console.error('Sign out failed:', error)
    }
}
</script>
