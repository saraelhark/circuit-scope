<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
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

const route = useRoute()

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
        class="sticky top-0 z-50 w-full bg-cs-light-green text-cs-charcoal font-primary border-b-4 border-cs-whiteish">
        <div class="container px-8 sm:px-16 flex h-14 items-center justify-between">
            <div class="flex items-center gap-4">
                <NuxtLink to="/"
                    class="flex items-center gap-2 text-xl font-bold text-cs-charcoal hover:opacity-80 transition-opacity">
                    <img class="h-8 w-8 rounded-lg" src="/logo.svg" alt="Circuit Scope logo" />
                    <span class="ml-4 text-cs-whiteish hidden sm:block">Circuit Scope</span>
                </NuxtLink>
            </div>

            <div class="flex items-center gap-1 sm:gap-4">
                <Button as="a" href="https://github.com/saraelhark/circuit-scope" target="_blank" rel="noreferrer"
                    variant="ghost" size="icon" class="text-cs-charcoal hover:opacity-80 hidden sm:inline-flex">
                    <i class="fab fa-github text-xl text-cs-dark-green"></i>
                    <span class="sr-only">Open Circuit Scope on GitHub</span>
                </Button>

                <template v-if="isSignedIn">
                    <NuxtLink to="/projects/new" v-if="route.path !== '/' && route.path !== '/projects/new'">
                        <button class="btn-regular text-sm py-1 px-3 h-9 flex items-center gap-2">
                            <span class="hidden sm:inline">Upload Project</span>
                            <i class="fas fa-plus sm:hidden"></i>
                        </button>
                    </NuxtLink>

                    <div class="relative" ref="notificationsRef">
                        <Button variant="ghost" size="icon" class="relative text-cs-charcoal hover:bg-cs-light-green/20"
                            @click="toggleNotifications">
                            <i class="fas fa-bell text-xl text-cs-dark-green"></i>
                            <span v-if="unreadCount > 0"
                                class="absolute top-2 right-2 h-2 w-2 rounded-full bg-cs-red"></span>
                        </Button>

                        <div v-if="isNotificationsOpen"
                            class="absolute right-0 mt-2 w-80 origin-top-right rounded-lg border bg-white shadow-lg focus:outline-none animate-in fade-in zoom-in-95 duration-200 max-h-[80vh] overflow-y-auto z-50 text-foreground font-secondary">
                            <div class="flex items-center justify-between px-4 py-3 border-b">
                                <h3 class="font-semibold text-sm">Notifications</h3>
                                <button v-if="unreadCount > 0" @click="markAllRead"
                                    class="text-xs text-cs-blue hover:underline">
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
                                    :class="{ 'bg-cs-light-green/10': !notification.is_read }">
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
                                            class="h-2 w-2 mt-1 rounded-full bg-cs-light-green shrink-0"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="relative" ref="userMenuRef">
                        <button @click="toggleUserMenu" class="flex items-center gap-2 outline-none">
                            <div
                                class="h-8 w-8 rounded-full bg-white flex items-center justify-center overflow-hidden text-cs-charcoal">
                                <img v-if="user?.image" :src="user.image" :alt="user.name || 'User'"
                                    class="h-full w-full object-cover" />
                                <i v-else class="fas fa-user h-4 w-4"></i>
                            </div>
                        </button>

                        <div v-if="isUserMenuOpen"
                            class="absolute right-0 mt-2 w-56 origin-top-right rounded-lg border bg-cs-light-green p-1 shadow-lg focus:outline-none animate-in fade-in zoom-in-95 duration-200 z-50 text-foreground font-secondary">
                            <NuxtLink to="/dashboard"
                                class="relative flex cursor-default select-none items-center rounded-sm p-2 text-sm outline-none hover:bg-cs-charcoal/10"
                                @click="isUserMenuOpen = false">
                                <i class="fas fa-folder mr-2 h-4 w-4"></i>
                                <span>My Projects</span>
                            </NuxtLink>
                            <div class="h-px my-1 bg-muted"></div>
                            <Button variant="ghost" @click="handleSignOut"
                                class="relative flex w-full cursor-default select-none items-center rounded-sm p-2 text-sm outline-none hover:bg-cs-charcoal/10 h-auto justify-start">
                                <i class="fas fa-right-from-bracket mr-2"></i>
                                <span>Sign out</span>
                            </Button>
                        </div>
                    </div>
                </template>

                <template v-else>
                    <NuxtLink to="/login">
                        <Button variant="special" class="text-sm h-9 pl-12">Login</Button>
                    </NuxtLink>
                </template>
            </div>
        </div>
    </header>
</template>
