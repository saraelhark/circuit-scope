import { proxyRequest } from 'h3'
import { getServerSession } from '#auth'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const backendBase = config.private.backendUrl
  const frontendToken = config.private.frontendSecretKey
  const targetUrl = new URL(event.node.req.url || '', backendBase).toString()

  const headers: Record<string, string> = {}

  if (frontendToken) {
    headers['x-frontend-token'] = frontendToken
  }

  const session = await getServerSession(event)
  const user = session?.user as any
  const email = user?.email as string | undefined

  if (email && frontendToken && backendBase) {
    try {
      const authSyncUrl = new URL('/api/v1/auth/sync', backendBase).toString()
      const backendUser = await $fetch<{ id: string }>(authSyncUrl, {
        method: 'POST',
        headers: {
          'x-frontend-token': frontendToken,
          'content-type': 'application/json',
        },
        body: {
          email,
          display_name: user?.name ?? null,
          avatar_url: user?.image ?? null,
        },
      })

      if (backendUser && backendUser.id) {
        headers['x-user-id'] = backendUser.id
      }
    } catch {
    }
  }

  console.log('Proxying request to backend', targetUrl)
  return await proxyRequest(event, targetUrl, {
    headers,
  })
})
