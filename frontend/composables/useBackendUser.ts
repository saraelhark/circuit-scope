import type { BackendUser } from "~/types/api/auth"

export const useBackendUser = () => {
    const { data: session, status } = useAuth()

    const backendUser = useState<BackendUser | null>("backendUser", () => null)
    const isSyncingBackendUser = useState<boolean>(
        "backendUserSyncing",
        () => false,
    )
    const backendUserError = useState<string | null>(
        "backendUserSyncError",
        () => null,
    )

    const syncBackendUser = async () => {
        if (import.meta.server) return

        if (status.value !== "authenticated") {
            backendUser.value = null
            return
        }

        const user: any = session.value?.user
        const email: string | undefined = user?.email

        if (!email) {
            return
        }

        if (isSyncingBackendUser.value) {
            return
        }

        isSyncingBackendUser.value = true
        backendUserError.value = null

        try {
            const result = await $fetch<BackendUser>("/api/v1/auth/sync", {
                method: "POST",
                body: {
                    email,
                    display_name: user?.name ?? null,
                    avatar_url: user?.image ?? null,
                },
            })

            backendUser.value = result
        } catch (error: any) {
            backendUserError.value =
                error?.data?.detail ?? error?.message ?? "Failed to sync user"
        } finally {
            isSyncingBackendUser.value = false
        }
    }

    watch(
        () => ({
            status: status.value,
            email: (session.value as any)?.user?.email as string | undefined,
        }),
        () => {
            void syncBackendUser()
        },
        { immediate: true },
    )

    return {
        backendUser,
        isSyncingBackendUser,
        backendUserError,
        syncBackendUser,
    }
}
