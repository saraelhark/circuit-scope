import { useRuntimeConfig, useRequestURL, useSeoMeta, useHead, defineOgImage } from '#imports'

interface AppSeoOptions {
    title?: string
    description?: string
    path?: string
    ogImage?: string
    schemaOrg?: Record<string, any> | Record<string, any>[]
}

export function useAppSeo(options: AppSeoOptions) {
    const config = useRuntimeConfig()
    const url = import.meta.client ? window.location.href : useRequestURL().href

    const siteUrl = (config.public as any).siteUrl as string
    const fullUrl = options.path ? new URL(options.path, siteUrl).toString() : url

    useSeoMeta({
        title: options.title,
        description: options.description,
        ogTitle: options.title,
        ogDescription: options.description,
        ogUrl: fullUrl,
        twitterTitle: options.title,
        twitterDescription: options.description,
    })

    if (options.schemaOrg) {
        const graph = Array.isArray(options.schemaOrg) ? options.schemaOrg : [options.schemaOrg]

        useHead({
            script: [
                {
                    type: 'application/ld+json',
                    innerHTML: JSON.stringify(graph),
                },
            ],
        })
    }
}
