// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: false },

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
    },
  },

  components: [
    {
      // To resolve the warning about multiple component files resolving to the same name
      path: '~/components',
      extensions: ['vue'],
    },
  ],

})