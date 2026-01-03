import type { PreviewAsset } from '~/types/api/projects'

export type ViewerKind = '2d' | '3d'

export type ViewerView = {
  id: string
  label: string
  asset?: PreviewAsset | null
  fallbackMessage?: string
  pages?: PreviewAsset[]
  layers?: PreviewAsset[]
  kind?: ViewerKind
}
