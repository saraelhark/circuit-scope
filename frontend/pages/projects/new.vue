<script setup lang="ts">
import { reactive, ref } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { Checkbox } from "~/components/ui/checkbox"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { Textarea } from "~/components/ui/textarea"
import { formatDateTime } from "~/lib/formatters"
import { normaliseStatus, statusVariant, visibilityLabel } from "~/lib/projects"
import { useProject } from "~/composables/useProjects"
import type { ProjectCreatePayload, ProjectUploadResponse } from "~/types/api/projects"

definePageMeta({
  layout: "default",
})

useHead({
  title: "New project – Circuit Scope",
})

const router = useRouter()
const { createProject } = useProject()

const form = reactive({
  name: "",
  description: "",
  isPublic: false,
})

const file = ref<File | null>(null)
const submitting = ref(false)
const submissionError = ref<string | null>(null)
const uploadResponse = ref<ProjectUploadResponse | null>(null)

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  file.value = target.files?.[0] ?? null
}

function resetPreview() {
  uploadResponse.value = null
}

async function handleSubmit() {
  submitting.value = true
  submissionError.value = null
  uploadResponse.value = null

  if (!form.name) {
    submissionError.value = "Project name is required."
    submitting.value = false
    return
  }

  try {
    const payload: ProjectCreatePayload = {
      name: form.name,
      description: form.description || undefined,
      is_public: form.isPublic || undefined,
    }

    const response = await createProject(payload, file.value ?? undefined)
    uploadResponse.value = response
    resetForm()
  } catch (error: any) {
    submissionError.value = error?.data?.detail ?? error?.message ?? "Failed to create project."
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.name = ""
  form.description = ""
  form.isPublic = false
  file.value = null
}

function goToProjectList() {
  router.push("/projects")
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
      <Button variant="outline" class="mx-auto sm:mx-0" @click="goToProjectList">
        Back to projects
      </Button>
    </div>

    <div class="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <form v-if="!uploadResponse" class="w-full" @submit.prevent="handleSubmit">
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
              <Label for="visibility">Visibility</Label>
              <div class="flex items-center gap-2 rounded-md border border-input bg-muted/20 px-3 py-2">
                <Checkbox id="visibility" v-model="form.isPublic" />
                <Label for="visibility" class="text-sm text-muted-foreground">
                  Make project public
                </Label>
              </div>
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

      <Card v-if="uploadResponse" class="h-fit">
        <CardHeader>
          <CardTitle>Project created</CardTitle>
          <CardDescription>
            The project has been created successfully.
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-3 text-sm text-muted-foreground">
          <div class="space-y-1">
            <p class="text-base font-semibold text-foreground">
              {{ uploadResponse.project.name }}
            </p>
            <Badge :variant="statusVariant(uploadResponse.project.status)">
              {{ normaliseStatus(uploadResponse.project.status) }}
            </Badge>
          </div>

          <dl class="space-y-1">
            <div class="flex items-center justify-between">
              <dt class="font-medium text-foreground">Owner</dt>
              <dd>{{ uploadResponse.project.owner_id }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="font-medium text-foreground">Visibility</dt>
              <dd>{{ visibilityLabel(uploadResponse.project) }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="font-medium text-foreground">Created</dt>
              <dd>{{ formatDateTime(uploadResponse.project.created_at) }}</dd>
            </div>
            <div class="flex items-center justify-between">
              <dt class="font-medium text-foreground">Updated</dt>
              <dd>{{ formatDateTime(uploadResponse.project.updated_at) }}</dd>
            </div>
          </dl>

          <div v-if="uploadResponse.upload_result" class="rounded-md border border-muted-foreground/40 px-3 py-2">
            <p class="text-xs uppercase tracking-wide text-muted-foreground">Upload</p>
            <p class="font-medium text-foreground">{{ uploadResponse.upload_result.filename }}</p>
            <p class="text-xs text-muted-foreground break-all">
              {{ uploadResponse.upload_result.storage_path }}
            </p>
          </div>
        </CardContent>
        <CardFooter class="flex flex-wrap gap-2">
          <Button asChild variant="secondary">
            <NuxtLink :to="`/projects/${uploadResponse.project.id}`">View project</NuxtLink>
          </Button>
          <Button variant="outline" @click="resetPreview">
            Create another
          </Button>
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
