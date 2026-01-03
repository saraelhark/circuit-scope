// @ts-check
import { createConfigForNuxt } from '@nuxt/eslint-config/flat'

export default createConfigForNuxt({
  features: {
    stylistic: true,
  },
}).append({
  rules: {
    // Nuxt pages/layouts use single-word names by convention
    'vue/multi-word-component-names': 'off',

    // Allow multiple template roots (Nuxt 3 supports fragments)
    'vue/no-multiple-template-root': 'off',

    // TypeScript - allow any in specific cases but encourage proper types
    '@typescript-eslint/no-explicit-any': 'off',

    // Allow void in union types for event emitters
    '@typescript-eslint/no-invalid-void-type': 'off',

    // Allow combining overloads (common pattern in Vue emit types)
    '@typescript-eslint/unified-signatures': 'off',

    // Nuxt auto-imports
    'no-undef': 'off',
  },
})
