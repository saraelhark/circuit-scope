<script setup lang="ts">
import { reactive, ref } from "vue"

import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
} from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { Textarea } from "~/components/ui/textarea"
import { useProject } from "~/composables/useProjects"
import type { ProjectCreatePayload } from "~/types/api/projects"

definePageMeta({
  layout: "default",
  middleware: "auth",
})

useHead({
  title: "New project – Circuit Scope",
})

const router = useRouter()
const { createProject } = useProject()
const { backendUser } = useBackendUser()

const MAX_ARCHIVE_SIZE_MB = 30
const MAX_ARCHIVE_SIZE_BYTES = MAX_ARCHIVE_SIZE_MB * 1024 * 1024

const form = reactive({
  name: "",
  description: "",
})

const file = ref<File | null>(null)
const submitting = ref(false)
const submissionError = ref<string | null>(null)

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const selected = target.files?.[0] ?? null

  submissionError.value = null

  if (selected && selected.size > MAX_ARCHIVE_SIZE_BYTES) {
    file.value = null
    submissionError.value = `KiCad archive must be ${MAX_ARCHIVE_SIZE_MB} MB or smaller.`
    return
  }

  file.value = selected
}

async function handleSubmit() {
  submitting.value = true
  submissionError.value = null

  if (!form.name) {
    submissionError.value = "Project name is required."
    submitting.value = false
    return
  }

  if (!backendUser.value || !backendUser.value.id) {
    submissionError.value = "You must be signed in to create a project."
    submitting.value = false
    return
  }

  try {
    const payload: ProjectCreatePayload = {
      name: form.name,
      description: form.description || undefined,
      owner_id: backendUser.value.id,
    }

    const response = await createProject(payload, file.value ?? undefined)
    router.push(`/projects/${response.project.id}`)
  } catch (error: any) {
    submissionError.value = error?.data?.detail ?? error?.message ?? "Failed to create project."
  } finally {
    submitting.value = false
  }
}

</script>

<template>
  <div class="min-h-screen flex justify-center items-start pt-16">
    <form class="w-full max-w-2xl" @submit.prevent="handleSubmit">
      <Card class="w-full py-12 px-16">
        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-white font-primary sm:text-2xl md:text-3xl">Upload a design for review</h1>
        </div>
        <div class="space-y-6">
          <div class="space-y-2">
            <Label for="name" class="text-white">Project name</Label>
            <Input id="name" v-model="form.name" placeholder="ESP32 IoT weather station" required
              class="bg-white text-cs-charcoal border-cs-whiteish" />
          </div>

          <div class="space-y-2">
            <Label for="description" class="text-white">Description</Label>
            <Textarea id="description" v-model="form.description"
              placeholder="Describe the project to give better context for the design review"
              class="bg-white text-cs-charcoal border-cs-whiteish" />
          </div>

          <div class="space-y-2">
            <Label for="file" class="text-white">Project archive</Label>
            <Input id="file" type="file" accept=".zip" @change="onFileChange"
              class="bg-white text-cs-charcoal border-cs-whiteish file:text-cs-charcoal cursor-pointer" />
            <p class="text-sm text-cs-whiteish/80">
              Upload a KiCad project archive (max {{ MAX_ARCHIVE_SIZE_MB }} MB).
              Only <code>.zip</code> files are supported.
            </p>
            <p v-if="file" class="text-xs text-cs-whiteish/80">
              Selected file: {{ file?.name }}
            </p>
          </div>

          <div v-if="submissionError" class="rounded-md border border-cs-red bg-cs-red/20 p-3 text-sm text-white">
            {{ submissionError }}
          </div>
        </div>
        <div class="mt-8 flex items-center justify-end gap-2">
          <Button variant="cta" type="submit" :disabled="submitting">
            <span v-if="submitting">Creating…</span>
            <span v-else>Submit</span>
          </Button>
        </div>
      </Card>
    </form>
  </div>
</template>
