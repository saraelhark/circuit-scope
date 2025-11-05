import type { PreviewAsset } from "~/types/api/projects"
import type { ViewerView } from "~/components/projects/ReviewCanvas.vue"

export function buildViewerViews(
    schematics: PreviewAsset[],
    layouts: PreviewAsset[],
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

    const topLayout =
        layouts.find((layout) => /top|front/i.test(layout.title ?? layout.id)) ?? layouts[0]
    const bottomLayout = layouts.find((layout) => /bottom|back/i.test(layout.title ?? layout.id))

    views.push({
        id: "pcb-top",
        label: "PCB Top",
        asset: topLayout ?? null,
        fallbackMessage: layouts.length
            ? "No top-side layout detected; showing first layout available."
            : "No PCB layout previews available.",
    })

    views.push({
        id: "pcb-bottom",
        label: "PCB Bottom",
        asset: bottomLayout ?? (layouts.length > 1 ? layouts[1] : null),
        fallbackMessage: layouts.length > 1
            ? "No bottom-side layout detected; showing alternative layout."
            : "No additional PCB layout previews available.",
    })

    return views
}
