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
    originEnvKey: 'http://localhost:3000/api/auth',
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
    public: {
      apiBase: "/api/v1",
    },
    private: {
      backendUrl: process.env.NUXT_PRIVATE_BACKEND_URL,
      frontendSecretKey: process.env.NUXT_PRIVATE_FRONTEND_SECRET_KEY,
      // Auth.js configuration
      authSecret: process.env.NUXT_AUTH_SECRET,
      googleClientId: process.env.NUXT_GOOGLE_CLIENT_ID,
      googleClientSecret: process.env.NUXT_GOOGLE_CLIENT_SECRET,
      githubClientId: process.env.NUXT_GITHUB_CLIENT_ID,
      githubClientSecret: process.env.NUXT_GITHUB_CLIENT_SECRET,
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