export default defineNuxtPlugin(() => {
  const isProd = process.env.NODE_ENV === 'production'
  const visitorId = useCookie('visitor_id', {
    maxAge: 60 * 60 * 24 * 30, // 1 month
    sameSite: 'lax',
    secure: isProd,
  })

  if (!visitorId.value) {
    visitorId.value = crypto.randomUUID()
  }
})
