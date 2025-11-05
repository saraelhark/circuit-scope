import type { CommentThread } from "~/types/api/commentThreads"
import type { ViewerAnnotation } from "~/components/projects/ReviewCanvas.vue"

export function mapThreadsToAnnotations(
    threads: CommentThread[],
): Record<string, ViewerAnnotation[]> {
    const map: Record<string, ViewerAnnotation[]> = {}

    for (const thread of threads) {
        const annotation = thread.annotation
        if (!annotation || annotation.tool !== "circle") continue

        const radius = Number((annotation.data as any)?.radius ?? 0)
        if (!Number.isFinite(radius) || radius <= 0) continue

        const entry: ViewerAnnotation = {
            id: thread.id,
            tool: "circle",
            pinX: thread.pin_x,
            pinY: thread.pin_y,
            data: { radius },
        }

        if (!entry) continue

        if (!map[thread.view_id]) {
            map[thread.view_id] = []
        }
        map[thread.view_id].push(entry)
    }

    return map
}
