import type {
  CommentThread,
  CommentThreadCreatePayload,
  CommentThreadListResponse,
  ThreadComment,
  ThreadCommentCreatePayload,
  ThreadResolutionUpdatePayload,
} from '~/types/api/commentThreads'

export function useCommentThreads() {
  const {
    public: { apiBase },
  } = useRuntimeConfig()

  const listThreads = (projectId: string) =>
    $fetch<CommentThreadListResponse>(`${apiBase}/projects/${projectId}/threads/`)

  const createThread = (projectId: string, payload: CommentThreadCreatePayload) =>
    $fetch<CommentThread>(`${apiBase}/projects/${projectId}/threads/`, {
      method: 'POST',
      body: payload,
    })

  const addComment = (
    projectId: string,
    threadId: string,
    payload: ThreadCommentCreatePayload,
  ) =>
    $fetch<ThreadComment>(`${apiBase}/projects/${projectId}/threads/${threadId}/comments`, {
      method: 'POST',
      body: payload,
    })

  const updateThreadResolution = (
    projectId: string,
    threadId: string,
    payload: ThreadResolutionUpdatePayload,
  ) =>
    $fetch<CommentThread>(`${apiBase}/projects/${projectId}/threads/${threadId}/resolution`, {
      method: 'PATCH',
      body: payload,
    })

  const deleteThread = (projectId: string, threadId: string) =>
    $fetch<void>(`${apiBase}/projects/${projectId}/threads/${threadId}`, {
      method: 'DELETE',
    })

  const deleteComment = (projectId: string, threadId: string, commentId: string) =>
    $fetch<void>(
      `${apiBase}/projects/${projectId}/threads/${threadId}/comments/${commentId}`,
      {
        method: 'DELETE',
      },
    )

  return {
    listThreads,
    createThread,
    addComment,
    updateThreadResolution,
    deleteThread,
    deleteComment,
  }
}
