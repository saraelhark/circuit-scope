export interface ProjectFile {
  id: string
  filename: string
  file_type: string | null
  storage_path: string
  created_at: string
}

export interface Project {
  id: string
  owner_id: string
  name: string
  description: string | null
  is_public: boolean
  status: string | null
  github_repo_url: string | null
  secret_link?: string | null
  created_at: string
  updated_at: string
  files: ProjectFile[]
}

export interface ProjectListResponse {
  items: Project[]
  total: number
  page: number
  size: number
}

export interface ProjectUploadResult {
  filename: string
  storage_path: string
}

export interface ProjectUploadResponse {
  project: Project
  upload_result: ProjectUploadResult | null
}

export interface ProjectCreatePayload {
  name: string
  description?: string | null
  is_public?: boolean
  github_repo_url?: string | null
}

export interface ProjectUpdatePayload {
  name?: string | null
  description?: string | null
  is_public?: boolean | null
  status?: string | null
  github_repo_url?: string | null
}

export interface ListProjectsQuery {
  page?: number
  size?: number
  only_public?: boolean
  owner_id?: string
}
