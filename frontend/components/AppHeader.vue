<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Bell, User, LogOut, Folder, Github, Check } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { onClickOutside } from '@vueuse/core'

const { data: session, status, signOut } = useAuth()
const { backendUser } = useBackendUser()
const user = computed(() => session.value?.user)
const isSignedIn = computed(() => status.value === 'authenticated')

const isUserMenuOpen = ref(false)
const userMenuRef = ref(null)

const isNotificationsOpen = ref(false)
const notificationsRef = ref(null)
const unreadCount = ref(0)
const notifications = ref<any[]>([])

function toggleUserMenu() {
    isUserMenuOpen.value = !isUserMenuOpen.value
    if (isUserMenuOpen.value) isNotificationsOpen.value = false
}

function toggleNotifications() {
    isNotificationsOpen.value = !isNotificationsOpen.value
    if (isNotificationsOpen.value) {
        isUserMenuOpen.value = false
        fetchNotifications()
    }
}

onClickOutside(userMenuRef, () => {
    isUserMenuOpen.value = false
})

onClickOutside(notificationsRef, () => {
    isNotificationsOpen.value = false
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

async function fetchUnreadCount() {
    if (!backendUser.value?.id) return
    try {
        const res = await $fetch<{ count: number }>('/api/v1/notifications/unread-count', {
            headers: { 'X-User-Id': backendUser.value.id }
        })
        unreadCount.value = res.count
    } catch (e) {
        console.error('Failed to fetch unread count', e)
    }
}

async function fetchNotifications() {
    if (!backendUser.value?.id) return
    try {
        notifications.value = await $fetch<any[]>('/api/v1/notifications', {
            headers: { 'X-User-Id': backendUser.value.id }
        })
    } catch (e) {
        console.error('Failed to fetch notifications', e)
    }
}

async function markAsRead(notification: any) {
    if (!backendUser.value?.id) return

    if (!notification.is_read) {
        notification.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)

        try {
            await $fetch(`/api/v1/notifications/${notification.id}/read`, {
                method: 'POST',
                headers: { 'X-User-Id': backendUser.value.id }
            })
        } catch (e) {
            console.error('Failed to mark as read', e)
        }
    }

    if (notification.project_id) {
        isNotificationsOpen.value = false
        // For thread/comment notifications, go to the review page
        if (notification.thread_id) {
            await navigateTo(`/projects/${notification.project_id}/review?thread=${notification.thread_id}`)
        } else {
            await navigateTo(`/projects/${notification.project_id}`)
        }
    }
}

async function markAllRead() {
    if (!backendUser.value?.id) return
    try {
        await $fetch('/api/v1/notifications/read-all', {
            method: 'POST',
            headers: { 'X-User-Id': backendUser.value.id }
        })
        unreadCount.value = 0
        notifications.value.forEach(n => n.is_read = true)
    } catch (e) {
        console.error('Failed to mark all read', e)
    }
}

let pollInterval: NodeJS.Timeout
onMounted(() => {
    if (backendUser.value?.id) fetchUnreadCount()
    pollInterval = setInterval(() => {
        if (backendUser.value?.id && !isNotificationsOpen.value) {
            fetchUnreadCount()
        }
    }, 30000) // 30s
})

watch(() => backendUser.value?.id, (newId) => {
    if (newId) fetchUnreadCount()
})

</script>

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
                <Button as="a" href="https://github.com/saraelhark/circuit-scope" target="_blank" rel="noreferrer"
                    variant="ghost" size="icon" class="text-muted-foreground hover:text-foreground">
                    <Github class="h-5 w-5" />
                    <span class="sr-only">Open Circuit Scope on GitHub</span>
                </Button>

                <template v-if="isSignedIn">
                    <NuxtLink to="/projects/new">
                        <Button size="sm">Upload Project</Button>
                    </NuxtLink>

                    <div class="relative" ref="notificationsRef">
                        <Button variant="ghost" size="icon" class="relative" @click="toggleNotifications">
                            <Bell class="h-5 w-5" />
                            <span v-if="unreadCount > 0"
                                class="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500"></span>
                        </Button>

                        <div v-if="isNotificationsOpen"
                            class="absolute right-0 mt-2 w-80 origin-top-right rounded-md border bg-popover shadow-md focus:outline-none animate-in fade-in zoom-in-95 duration-200 max-h-[80vh] overflow-y-auto z-50">
                            <div class="flex items-center justify-between px-4 py-3 border-b">
                                <h3 class="font-semibold text-sm">Notifications</h3>
                                <button v-if="unreadCount > 0" @click="markAllRead"
                                    class="text-xs text-primary hover:underline">
                                    Mark all read
                                </button>
                            </div>

                            <div v-if="notifications.length === 0"
                                class="p-4 text-center text-sm text-muted-foreground">
                                No notifications
                            </div>

                            <div v-else class="divide-y">
                                <div v-for="notification in notifications" :key="notification.id"
                                    @click="markAsRead(notification)"
                                    class="p-3 hover:bg-accent cursor-pointer transition-colors text-sm"
                                    :class="{ 'bg-primary/5': !notification.is_read }">
                                    <div class="flex gap-3">
                                        <div class="flex-1 space-y-1">
                                            <p class="leading-none" :class="{ 'font-medium': !notification.is_read }">
                                                {{ notification.message }}
                                            </p>
                                            <p class="text-xs text-muted-foreground">
                                                {{ new Date(notification.created_at).toLocaleDateString() }}
                                            </p>
                                        </div>
                                        <div v-if="!notification.is_read"
                                            class="h-2 w-2 mt-1 rounded-full bg-primary shrink-0"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
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
                            class="absolute right-0 mt-2 w-56 origin-top-right rounded-md border bg-popover p-1 shadow-md focus:outline-none animate-in fade-in zoom-in-95 duration-200 z-50">
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
</template>>
