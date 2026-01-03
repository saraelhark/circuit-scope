import type { PreviewAsset } from '~/types/api/projects'
import type { ViewerView } from '~/types/viewer'

export function buildViewerViews(
  schematics: PreviewAsset[],
  layouts: PreviewAsset[],
  models: PreviewAsset[] = [],
): ViewerView[] {
  const views: ViewerView[] = []

  if (schematics.length) {
    views.push({
      id: 'schematic',
      label: 'Schematic',
      asset: schematics[0],
      fallbackMessage: 'No schematic SVG generated yet.',
    })
  }
  else {
    views.push({
      id: 'schematic',
      label: 'Schematic',
      asset: undefined,
      fallbackMessage: 'No schematic previews available.',
    })
  }

  const topLayout = layouts.find(layout => layout.id === 'front') || layouts.find(layout => /top|front/i.test(layout.title ?? ''))
  const bottomLayout = layouts.find(layout => layout.id === 'back') || layouts.find(layout => /bottom|back/i.test(layout.title ?? ''))

  const innerLayers = layouts.filter(layout => layout.id.startsWith('inner-'))
  innerLayers.sort((a, b) => {
    const aIdx = parseInt(a.id.split('-')[1] || '0')
    const bIdx = parseInt(b.id.split('-')[1] || '0')
    return aIdx - bIdx
  })

  const pcbLayers: PreviewAsset[] = []
  if (topLayout) pcbLayers.push(topLayout)
  pcbLayers.push(...innerLayers)
  if (bottomLayout) pcbLayers.push(bottomLayout)

  if (pcbLayers.length > 0) {
    views.push({
      id: 'pcb-layout',
      label: 'PCB Layout',
      asset: topLayout ?? pcbLayers[0],
      layers: pcbLayers,
      fallbackMessage: 'No PCB layout previews available.',
    })
  }
  else {
    views.push({
      id: 'pcb-layout',
      label: 'PCB Layout',
      asset: null,
      fallbackMessage: 'No PCB layout previews available.',
    })
  }

  const modelAsset = models[0]
  if (modelAsset) {
    views.push({
      id: 'pcb-3d',
      label: '3D Model',
      asset: modelAsset,
      fallbackMessage: 'No 3D model preview available.',
      kind: '3d',
    })
  }

  return views
}

export function buildReviewViews(
  sourceType: string | undefined,
  schematics: PreviewAsset[],
  layouts: PreviewAsset[],
  models: PreviewAsset[] = [],
  photos: PreviewAsset[] = [],
): ViewerView[] {
  const shouldUsePhotos
    = sourceType === 'images' || (!schematics.length && !layouts.length && photos.length > 0)

  if (shouldUsePhotos) {
    if (!photos.length) {
      return [
        {
          id: 'photos',
          label: 'Photos',
          asset: null,
          fallbackMessage: 'No photos uploaded.',
        },
      ]
    }

    return photos.map((photo, index) => ({
      id: `photo-${photo.id ?? index}`,
      label: photo.title || `Photo ${index + 1}`,
      asset: photo,
      fallbackMessage: 'Photo not available.',
    }))
  }

  return buildViewerViews(schematics, layouts, models)
}
