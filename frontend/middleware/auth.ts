export default defineNuxtRouteMiddleware(async (_to, _from) => {
  const { status, data: session } = useAuth()

  if (status.value === 'loading') {
    return
  }

  if (status.value === 'unauthenticated' || !session.value) {
    return navigateTo('/login')
  }
})
