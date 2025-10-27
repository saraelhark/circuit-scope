import { proxyRequest } from 'h3'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const backendBase = config.private.backendUrl
  // Preserve full path and query string when forwarding
  const targetUrl = new URL(event.node.req.url!, backendBase).toString()
  console.log('Proxying request to backend', targetUrl)
  return await proxyRequest(event, targetUrl)
})
