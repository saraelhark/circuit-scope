import GoogleProvider from 'next-auth/providers/google'
import GitHubProvider from 'next-auth/providers/github'
import { NuxtAuthHandler } from '#auth'

export default NuxtAuthHandler({
    secret: useRuntimeConfig().private.authSecret as string,

    providers: [
        (GoogleProvider as any).default({
            clientId: useRuntimeConfig().private.googleClientId as string,
            clientSecret: useRuntimeConfig().private.googleClientSecret as string,
        }) as any,

        (GitHubProvider as any).default({
            clientId: useRuntimeConfig().private.githubClientId as string,
            clientSecret: useRuntimeConfig().private.githubClientSecret as string,
        }) as any,
    ],

    callbacks: {
        async redirect({ url, baseUrl }) {
            if (url.startsWith("/")) return `${baseUrl}${url}`
            else if (new URL(url).origin === baseUrl) return url
            return baseUrl
        },

        async session({ session, token }) {
            if (token?.sub && session?.user) {
                (session.user as any).id = token.sub
            }
            return session
        },

        async jwt({ token, user, account }) {
            if (account && user) {
                return {
                    ...token,
                    accessToken: account.access_token,
                }
            }
            return token
        },
    },

    pages: {
        signIn: '/login',
        error: '/auth/error',
    },
})
