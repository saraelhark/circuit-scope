// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',

  modules: [
    '@sidebase/nuxt-auth',
    ['nuxt-og-image', {
      inline: true,
      component: 'OgTemplate'
    }],
  ],

  site: {
    url: 'https://circuitscope.io',
    name: 'Circuit Scope'
  },

  auth: {
    isEnabled: true,
    disableServerSideAuth: false,
    provider: {
      type: 'authjs'
    },
  },

  app: {
    head: {
      titleTemplate: '%s',
      meta: [
        { name: 'description', content: 'Circuit Scope lets makers share PCB designs—from full KiCad projects to board photos—and crowdsource schematic and layout reviews.' },
        { property: 'og:site_name', content: 'Circuit Scope' },
        { property: 'og:type', content: 'website' },
        { name: 'twitter:card', content: 'summary_large_image' },
      ],
    },
  },

  css: ['~/assets/css/main.css'],
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },

  runtimeConfig: {
    authSecret: '', // will be overridden by NUXT_AUTH_SECRET
    public: {
      apiBase: "/api/v1",
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL,
      deployLastmod: process.env.NUXT_PUBLIC_DEPLOY_LASTMOD || new Date().toISOString(),
      posthogPublicKey: process.env.NUXT_PUBLIC_POSTHOG_PUBLIC_KEY,
      posthogHost: process.env.NUXT_PUBLIC_POSTHOG_HOST,
    },
    private: {
      backendUrl: '',
      frontendSecretKey: '',
      // Auth.js configuration
      authOrigin: '',
      googleClientId: '',
      googleClientSecret: '',
      githubClientId: '',
      githubClientSecret: '',
    },
  },

  vite: {
    build: {
      minify: true,
      sourcemap: process.env.NODE_ENV !== "production",
      rollupOptions: {
        output: {
          manualChunks: undefined,
        },
      },
    },
    esbuild: {
      drop: process.env.NODE_ENV === "production" ? ["console"] : [],
    },
  },

  components: [
    {
      path: '~/components',
      extensions: ['vue'],
    },
  ],

})