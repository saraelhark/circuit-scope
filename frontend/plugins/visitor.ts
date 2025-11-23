export default defineNuxtPlugin(() => {
    const visitorId = useCookie('visitor_id', {
        maxAge: 60 * 60 * 24 * 365, // 1 year
        sameSite: 'lax',
        secure: false // Set to true in production if https
    })

    if (!visitorId.value) {
        visitorId.value = crypto.randomUUID()
    }
})
