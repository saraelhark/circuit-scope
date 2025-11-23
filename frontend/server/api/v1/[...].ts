import { proxyRequest } from 'h3'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const backendBase = config.private.backendUrl
  const frontendToken = config.private.frontendSecretKey
  const targetUrl = new URL(event.node.req.url!, backendBase).toString()

  const headers: Record<string, string> = {}

  if (frontendToken) {
    headers['x-frontend-token'] = frontendToken
  }

  console.log('Proxying request to backend', targetUrl)
  return await proxyRequest(event, targetUrl, {
    headers
  })
})
