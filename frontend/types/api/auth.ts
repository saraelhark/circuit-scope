export interface BackendUser {
    id: string
    email: string | null
    display_name: string | null
    avatar_url: string | null
    is_active: boolean
    created_at: string
    updated_at: string
}
