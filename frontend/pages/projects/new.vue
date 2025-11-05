<script setup lang="ts">
import { reactive, ref } from "vue"

import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
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

const form = reactive({
  name: "",
  description: "",
})

const file = ref<File | null>(null)
const submitting = ref(false)
const submissionError = ref<string | null>(null)

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  file.value = target.files?.[0] ?? null
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
  <div class="mx-auto flex max-w-5xl flex-col gap-6">
    <div class="flex flex-wrap items-center justify-between gap-4 text-center sm:text-left">
      <div class="mx-auto sm:mx-0">
        <h1 class="text-3xl font-semibold tracking-tight">Create a new project</h1>
        <p class="text-muted-foreground">
          Share your KiCad PCB project for review.
        </p>
      </div>
    </div>

    <div class="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <form class="w-full" @submit.prevent="handleSubmit">
        <Card>
          <CardHeader>
            <CardTitle>Project details</CardTitle>
            <CardDescription>
              Provide metadata and optionally attach a KiCad ZIP archive.
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-6">
            <div class="space-y-2">
              <Label for="name">Project name</Label>
              <Input id="name" v-model="form.name" placeholder="My KiCad design" required />
            </div>

            <div class="space-y-2">
              <Label for="description">Description</Label>
              <Textarea id="description" v-model="form.description"
                placeholder="Describe the purpose, scope, and key components of this design." />
            </div>

            <div class="space-y-2">
              <Label for="file">Project archive</Label>
              <Input id="file" type="file" accept=".zip" @change="onFileChange" />
              <p class="text-sm text-muted-foreground">
                Upload a KiCad ZIP archive. Only <code>.zip</code> files are supported.
              </p>
              <p v-if="file" class="text-xs text-muted-foreground">
                Selected file: {{ file?.name }}
              </p>
            </div>

            <div v-if="submissionError"
              class="rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              {{ submissionError }}
            </div>
          </CardContent>
          <CardFooter class="flex items-center justify-end gap-2">
            <Button type="submit" :disabled="submitting">
              <span v-if="submitting">Creating…</span>
              <span v-else>Submit project</span>
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  </div>
</template>
