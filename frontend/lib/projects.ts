import type { Project } from "~/types/api/projects"

const SUCCESS_STATUSES = new Set(["published", "ready", "complete", "processed"])
const WARNING_STATUSES = new Set(["processing", "queued", "pending", "in_progress"])
const DESTRUCTIVE_STATUSES = new Set(["failed", "error", "rejected"])
const SECONDARY_STATUSES = new Set(["draft", "created"])

export function normaliseStatus(status: Project["status"]) {
  return status?.replace(/_/g, " ") ?? "unknown"
}

export function statusVariant(status: Project["status"]) {
  if (!status) return "muted"
  const normalized = status.toLowerCase()
  if (SUCCESS_STATUSES.has(normalized)) return "success"
  if (WARNING_STATUSES.has(normalized)) return "warning"
  if (DESTRUCTIVE_STATUSES.has(normalized)) return "destructive"
  if (SECONDARY_STATUSES.has(normalized)) return "secondary"
  return "muted"
}

export function visibilityLabel(project: Project) {
  return project.is_public ? "Public" : "Private"
}
