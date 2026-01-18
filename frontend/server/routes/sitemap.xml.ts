import { defineEventHandler } from 'h3'
import { $fetch } from 'ofetch'
import { useRuntimeConfig } from '#imports'

interface ProjectListResponse {
  items: { id: string, slug?: string | null, updated_at?: string | null }[]
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const siteUrl = (config.public as any).siteUrl as string
  const deployLastmod = (config.public as any).deployLastmod as string | undefined
  const backendUrl = (config.private as any).backendUrl as string | undefined
  const frontendToken = (config.private as any).frontendSecretKey as string | undefined

  const staticUrls: { loc: string, lastmod?: string, priority?: number }[] = [
    { loc: new URL('/', siteUrl).toString(), lastmod: deployLastmod, priority: 1.0 },
    { loc: new URL('/privacy', siteUrl).toString(), lastmod: deployLastmod },
    { loc: new URL('/tos', siteUrl).toString(), lastmod: deployLastmod },
  ]

  let projectPaths: { loc: string, lastmod?: string }[] = []

  if (backendUrl) {
    try {
      const headers: Record<string, string> = {}
      if (frontendToken) {
        headers['x-frontend-token'] = frontendToken
      }

      const data = await $fetch<ProjectListResponse>(`${backendUrl}/api/v1/projects`, {
        query: { size: 200 },
        headers,
      })

      projectPaths = (data.items || []).map(p => ({
        loc: new URL(`/projects/${p.id}/review`, siteUrl).toString(),
        // Use the project's last activity timestamp as lastmod
        lastmod: p.updated_at || undefined,
      }))
    }
    catch (e) {
      // Ignore sitemap project fetch errors to avoid breaking the route
      console.error('Failed to build project sitemap entries', e)
    }
  }

  const urls = [
    ...staticUrls,
    ...projectPaths,
  ]

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n`
    + `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`
    + urls
      .map((u) => {
        const lastmodTag = (u as any).lastmod ? `<lastmod>${(u as any).lastmod}</lastmod>` : ''
        const priorityTag = typeof (u as any).priority === 'number' ? `<priority>${(u as any).priority.toFixed(1)}</priority>` : ''
        return `<url><loc>${u.loc}</loc>${lastmodTag}${priorityTag}</url>`
      })
      .join('')
      + `</urlset>`

  event.node.res.setHeader('content-type', 'application/xml')
  return body
})
