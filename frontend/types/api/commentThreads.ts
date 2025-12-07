export type AnnotationTool = "pin"

export interface ThreadAnnotation {
  tool: AnnotationTool
  data: Record<string, unknown>
}

export interface ThreadAuthor {
  id: string
  display_name: string | null
  avatar_url: string | null
}

export interface ThreadComment {
  id: string
  thread_id: string
  parent_id: string | null
  author_id: string | null
  author: ThreadAuthor | null
  guest_name: string | null
  guest_email: string | null
  content: string
  created_at: string
  updated_at: string
}

export interface CommentThread {
  id: string
  project_id: string
  view_id: string
  pin_x: number
  pin_y: number
  annotation: ThreadAnnotation | null
  is_resolved: boolean
  created_by_id: string | null
  resolved_by_id: string | null
  resolved_at: string | null
  created_at: string
  updated_at: string
  comments: ThreadComment[]
  comment_count: number
}

export interface CommentThreadListResponse {
  project_id: string
  items: CommentThread[]
  total_count: number
  open_count: number
  resolved_count: number
}

export interface InitialThreadCommentPayload {
  content: string
  author_id?: string | null
  guest_name?: string | null
  guest_email?: string | null
}

export interface CommentThreadCreatePayload {
  view_id: string
  pin_x: number
  pin_y: number
  created_by_id?: string | null
  annotation?: ThreadAnnotation | null
  initial_comment: InitialThreadCommentPayload
}

export interface ThreadCommentCreatePayload {
  content: string
  parent_id?: string | null
  author_id?: string | null
  guest_name?: string | null
  guest_email?: string | null
}

export interface ThreadResolutionUpdatePayload {
  is_resolved: boolean
  resolved_by_id?: string | null
}
