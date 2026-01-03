import type {
  ListProjectsQuery,
  Project,
  ProjectCreatePayload,
  ProjectListResponse,
  ProjectUploadResponse,
  ProjectPreviewResponse,
} from '~/types/api/projects'

export interface ProjectUpdatePayload {
  name?: string | null
  description?: string | null
  is_public?: boolean | null
  status?: string | null
}

export function useProject() {
  const {
    public: { apiBase },
  } = useRuntimeConfig()

  const listProjects = (query: ListProjectsQuery = {}) =>
    $fetch<ProjectListResponse>(`${apiBase}/projects/`, { query })

  const getProject = (id: string) => $fetch<Project>(`${apiBase}/projects/${id}`)

  const getProjectPreviews = (id: string) =>
    $fetch<ProjectPreviewResponse>(`${apiBase}/projects/${id}/previews`)

  const createProject = (payload: ProjectCreatePayload, upload?: File, images?: File[]) => {
    const formData = new FormData()
    formData.append('project_data', JSON.stringify(payload))
    if (upload) {
      formData.append('upload', upload)
    }

    if (images && images.length) {
      for (const image of images) {
        formData.append('images', image)
      }
    }

    return $fetch<ProjectUploadResponse>(`${apiBase}/projects/`, {
      method: 'POST',
      body: formData,
    })
  }

  const updateProject = (id: string, payload: ProjectUpdatePayload) =>
    $fetch<Project>(`${apiBase}/projects/${id}`, {
      method: 'PATCH',
      body: payload,
    })

  const deleteProject = (id: string) =>
    $fetch<void>(`${apiBase}/projects/${id}`, { method: 'DELETE' })

  return {
    listProjects,
    getProject,
    getProjectPreviews,
    createProject,
    updateProject,
    deleteProject,
  }
}
