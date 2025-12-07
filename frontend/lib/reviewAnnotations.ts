import type { CommentThread } from "~/types/api/commentThreads"
import type { ViewerAnnotation } from "~/components/projects/ReviewCanvas.vue"

export function mapThreadsToAnnotations(
    threads: CommentThread[],
    authorColors?: Map<string, string>
): Record<string, ViewerAnnotation[]> {
    const map: Record<string, ViewerAnnotation[]> = {}

    for (const thread of threads) {
        const annotation = thread.annotation
        if (!annotation) continue

        const firstComment = thread.comments[0]
        const authorName = firstComment?.author?.display_name || firstComment?.guest_name || "Guest"
        const authorKey = firstComment?.author_id || firstComment?.guest_name || "Anonymous"

        const initial = authorName.charAt(0).toUpperCase()
        const commentPreview = firstComment?.content || ""
        const color = authorColors?.get(authorKey)

        const entry: ViewerAnnotation = {
            id: thread.id,
            tool: "pin",
            pinX: thread.pin_x,
            pinY: thread.pin_y,
            data: {
                initial,
                comment: commentPreview,
                authorName,
                color
            },
        }

        if (!map[thread.view_id]) {
            map[thread.view_id] = []
        }
        map[thread.view_id].push(entry)
    }

    return map
}
