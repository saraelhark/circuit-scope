import { defineNuxtPlugin } from '#app'
import posthog from 'posthog-js'

export default defineNuxtPlugin(() => {
  if (process.env.NODE_ENV === 'production') {
    const runtimeConfig = useRuntimeConfig()
    const posthogClient = posthog.init(runtimeConfig.public.posthogPublicKey, {
      api_host: runtimeConfig.public.posthogHost,
      defaults: runtimeConfig.public.posthogDefaults,
      person_profiles: 'always',
      loaded: (posthog) => {
        if (import.meta.env.MODE === 'development') posthog.debug()
      },
    })

    return {
      provide: {
        posthog: () => posthogClient,
      },
    }
  }
})
