<script setup lang="ts">
import { Card } from '~/components/ui/card'
import GithubIcon from '~/components/ui/icons/GithubIcon.vue'
import GoogleIcon from '~/components/ui/icons/GoogleIcon.vue'

const { signIn, status, data: session } = useAuth()

watch(session, (newSession) => {
  if (newSession) {
    navigateTo('/dashboard')
  }
}, { immediate: true })

defineOgImageComponent('OgTemplate', {
  heading: 'Sign In',
  description: 'Join the Circuit Scope community to share and review PCB designs.',
})
</script>

<template>
  <div class="min-h-screen flex justify-center items-start pt-16">
    <Card class="max-w-2xl w-full py-12 px-16">
      <div>
        <h2 class="mt-4 text-center text-2xl font-bold text-white font-primary sm:text-2xl md:text-3xl">
          Sign in to Circuit Scope
        </h2>
        <p class="mt-4 text-center text-sm text-cs-whiteish">
          Join the community to share and review PCB designs
        </p>
      </div>

      <div class="mt-4 space-y-4">
        <button
          :disabled="status === 'loading'"
          class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-gray-800 hover:bg-gray-700 disabled:opacity-50"
          @click="signIn('github')"
        >
          <GithubIcon class="w-5 h-5 mr-2" />
          {{ status === 'loading' ? 'Signing in...' : 'Continue with GitHub' }}
        </button>

        <button
          :disabled="status === 'loading'"
          class="group relative w-full flex justify-center py-3 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          @click="signIn('google')"
        >
          <GoogleIcon class="w-5 h-5 mr-2" />
          {{ status === 'loading' ? 'Signing in...' : 'Continue with Google' }}
        </button>
      </div>

      <div class="text-center mt-4">
        <p class="text-sm text-cs-whiteish">
          By signing in, you agree to our <NuxtLink to="/tos">terms of service</NuxtLink> and <NuxtLink
            to="/privacy"
          >privacy policy</NuxtLink>.
        </p>
      </div>
    </Card>
  </div>
</template>
