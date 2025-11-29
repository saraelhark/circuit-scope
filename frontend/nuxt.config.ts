// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: false },

  modules: [
    '@sidebase/nuxt-auth'
  ],

  auth: {
    isEnabled: true,
    disableServerSideAuth: false,
    provider: {
      type: 'authjs'
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