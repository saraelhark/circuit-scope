export default defineNuxtRouteMiddleware(async (to, from) => {
    const { status, data: session } = useAuth();

    if (status.value === 'loading') {
        return;
    }

    if (status.value === 'unauthenticated' || !session.value) {
        return navigateTo('/login');
    }
});
