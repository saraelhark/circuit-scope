import type { PreviewAsset } from "~/types/api/projects"
import type { ViewerView } from "~/types/viewer"

export function buildViewerViews(
    schematics: PreviewAsset[],
    layouts: PreviewAsset[],
    models: PreviewAsset[] = [],
): ViewerView[] {
    const views: ViewerView[] = []

    if (schematics.length) {
        views.push({
            id: "schematic",
            label: "Schematic",
            asset: schematics[0],
            fallbackMessage: "No schematic SVG generated yet.",
        })
    } else {
        views.push({
            id: "schematic",
            label: "Schematic",
            asset: undefined,
            fallbackMessage: "No schematic previews available.",
        })
    }

    const topLayout = layouts.find((layout) => layout.id === "front") || layouts.find((layout) => /top|front/i.test(layout.title ?? ""))
    const bottomLayout = layouts.find((layout) => layout.id === "back") || layouts.find((layout) => /bottom|back/i.test(layout.title ?? ""))

    const innerLayers = layouts.filter((layout) => layout.id.startsWith("inner-"))
    innerLayers.sort((a, b) => {
        const aIdx = parseInt(a.id.split("-")[1] || "0")
        const bIdx = parseInt(b.id.split("-")[1] || "0")
        return aIdx - bIdx
    })

    views.push({
        id: "pcb-top",
        label: "PCB Top",
        asset: topLayout ?? null,
        fallbackMessage: layouts.length
            ? "No top-side layout detected."
            : "No PCB layout previews available.",
    })

    innerLayers.forEach((layer) => {
        views.push({
            id: layer.id,
            label: layer.title || `Inner ${layer.id}`,
            asset: layer,
            fallbackMessage: "Layer preview not available.",
        })
    })

    views.push({
        id: "pcb-bottom",
        label: "PCB Bottom",
        asset: bottomLayout ?? null,
        fallbackMessage: layouts.length
            ? "No bottom-side layout detected."
            : "No additional PCB layout previews available.",
    })

    const modelAsset = models[0]
    if (modelAsset) {
        views.push({
            id: "pcb-3d",
            label: "3D Model",
            asset: modelAsset,
            fallbackMessage: "No 3D model preview available.",
            kind: "3d",
        })
    }

    return views
}
