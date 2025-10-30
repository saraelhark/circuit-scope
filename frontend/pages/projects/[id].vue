<script setup lang="ts">
import { computed, ref, watch } from "vue"

import { Badge } from "~/components/ui/badge"
import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { formatDateTime } from "~/lib/formatters"
import { normaliseStatus, statusVariant, visibilityLabel } from "~/lib/projects"
import type { Project, ProjectPreviewResponse } from "~/types/api/projects"
import { useProject } from "~/composables/useProjects"

definePageMeta({
  layout: "default",
})

const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.id as string)

const { getProject, getProjectPreviews } = useProject()

const { data, error, refresh, status } = useAsyncData<Project>(
  `project-${projectId.value}`,
  () => getProject(projectId.value),
  {
    watch: [projectId],
  },
)

const project = computed(() => data.value)

const { data: previewData, status: previewStatus } = useAsyncData<ProjectPreviewResponse>(
  `project-${projectId.value}-previews`,
  () => getProjectPreviews(projectId.value),
  {
    watch: [projectId],
  },
)

const previews = computed(() => previewData.value)

const schematics = computed(() => previews.value?.schematics ?? [])
const layouts = computed(() => previews.value?.layouts ?? [])
const models = computed(() => previews.value?.models ?? [])
const projectMetadata = computed<Record<string, unknown>>(
  () => (previews.value?.project as Record<string, unknown> | undefined) ?? {},
)

const schematicIndex = ref(0)
const layoutIndex = ref(0)

const activeSchematic = computed(() => schematics.value[schematicIndex.value])
const activeLayout = computed(() => layouts.value[layoutIndex.value])

const metadataEntries = computed(() =>
  Object.entries(projectMetadata.value).filter(([, value]) => value !== null && value !== undefined && value !== ""),
)

watch(
  schematics,
  (list) => {
    schematicIndex.value = list.length ? Math.min(schematicIndex.value, list.length - 1) : 0
  },
  { immediate: true },
)

watch(
  layouts,
  (list) => {
    layoutIndex.value = list.length ? Math.min(layoutIndex.value, list.length - 1) : 0
  },
  { immediate: true },
)

function cycleSchematic(direction: number) {
  const list = schematics.value
  if (!list.length) return
  schematicIndex.value = (schematicIndex.value + direction + list.length) % list.length
}

function selectSchematic(index: number) {
  if (index >= 0 && index < schematics.value.length) {
    schematicIndex.value = index
  }
}

function selectLayout(index: number) {
  if (index >= 0 && index < layouts.value.length) {
    layoutIndex.value = index
  }
}

useHead(() => ({
  title: project.value ? `${project.value.name} – Project – Circuit Scope` : "Project – Circuit Scope",
}))

function goBack() {
  router.back()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="space-y-1">
        <Button variant="ghost" class="-ml-2 text-sm" @click="goBack">
          ← Back
        </Button>
        <h1 class="text-3xl font-semibold tracking-tight">Project details</h1>
        <p class="text-muted-foreground">Review the project's metadata and uploaded files.</p>
      </div>

      <div v-if="project" class="flex items-center gap-2">
        <Badge :variant="statusVariant(project.status)">
          {{ normaliseStatus(project.status) }}
        </Badge>
        <span class="text-sm text-muted-foreground">Updated {{ formatDateTime(project.updated_at) }}</span>
      </div>
    </div>

    <Card v-if="error">
      <CardHeader>
        <CardTitle class="text-xl">Failed to load project</CardTitle>
        <CardDescription>{{ error?.message ?? "Please try again later." }}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="secondary" @click="refresh">
          Retry
        </Button>
      </CardContent>
    </Card>

    <div v-else>
      <div v-if="status === 'pending'" class="flex h-32 items-center justify-center text-muted-foreground">
        Loading project…
      </div>

      <div v-else-if="!project"
        class="rounded-lg border border-dashed border-muted-foreground/30 p-6 text-center text-sm text-muted-foreground">
        Project not found.
      </div>

      <div v-else class="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card class="lg:col-span-2">
          <CardHeader>
            <CardTitle class="text-2xl">{{ project.name }}</CardTitle>
            <CardDescription v-if="project.description" class="max-w-prose">
              {{ project.description }}
            </CardDescription>
          </CardHeader>
          <CardContent class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2">
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Owner:</span>
                {{ project.owner_id }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Visibility:</span>
                {{ visibilityLabel(project) }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Created:</span>
                {{ formatDateTime(project.created_at) }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Updated:</span>
                {{ formatDateTime(project.updated_at) }}
              </p>
            </div>
            <div class="space-y-2">
              <p v-if="project.github_repo_url" class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">GitHub:</span>
                <a class="underline" :href="project.github_repo_url" target="_blank" rel="noopener">
                  {{ project.github_repo_url }}
                </a>
              </p>
              <p v-if="project.secret_link" class="text-sm text-muted-foreground break-all">
                <span class="font-medium text-foreground">Secret link:</span>
                {{ project.secret_link }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Status:</span>
                {{ normaliseStatus(project.status) }}
              </p>
              <p class="text-sm text-muted-foreground">
                <span class="font-medium text-foreground">Files:</span>
                {{ project.files.length }}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card class="lg:col-span-2">
          <CardHeader>
            <CardTitle>Previews</CardTitle>
            <CardDescription>
              Automatically generated assets from the uploaded KiCad archive.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="previewStatus === 'pending'"
              class="flex h-40 items-center justify-center text-sm text-muted-foreground">
              Generating previews…
            </div>
            <div v-else class="space-y-10">
              <section class="space-y-3">
                <div class="flex items-center justify-between">
                  <h3 class="text-sm font-medium text-muted-foreground">Schematic</h3>
                  <div v-if="schematics.length > 1" class="flex items-center gap-2">
                    <Button size="sm" variant="outline" @click="cycleSchematic(-1)">
                      ‹ Prev
                    </Button>
                    <Button size="sm" variant="outline" @click="cycleSchematic(1)">
                      Next ›
                    </Button>
                  </div>
                </div>

                <div v-if="schematics.length" class="space-y-3">
                  <div class="rounded-lg border bg-white p-4 shadow-sm">
                    <img
                      v-if="activeSchematic?.url"
                      :src="activeSchematic.url"
                      :alt="activeSchematic?.title || 'Schematic sheet'"
                      class="mx-auto max-h-[520px] w-full max-w-full object-contain"
                    />
                  </div>
                  <div class="flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
                    <div class="space-x-2">
                      <span class="font-medium text-foreground">{{ activeSchematic?.title ?? "Schematic" }}</span>
                      <span v-if="activeSchematic?.page">Page {{ activeSchematic.page }}</span>
                    </div>
                    <a
                      v-if="activeSchematic?.url"
                      :href="activeSchematic.url"
                      target="_blank"
                      rel="noopener"
                      class="underline"
                    >
                      Open full size
                    </a>
                  </div>
                  <div v-if="schematics.length > 1" class="flex flex-wrap gap-2">
                    <button
                      v-for="(sheet, index) in schematics"
                      :key="sheet.id"
                      type="button"
                      class="rounded-md border px-3 py-1 text-xs transition hover:bg-muted"
                      :class="index === schematicIndex ? 'border-primary bg-primary/5 text-primary' : 'border-border text-muted-foreground'"
                      @click="selectSchematic(index)"
                    >
                      {{ sheet.title || `Sheet ${index + 1}` }}
                    </button>
                  </div>
                </div>
                <p v-else class="text-sm text-muted-foreground">No schematic previews available.</p>
              </section>

              <section class="space-y-3">
                <div class="flex items-center justify-between">
                  <h3 class="text-sm font-medium text-muted-foreground">PCB layout</h3>
                  <div v-if="layouts.length > 1" class="flex gap-2">
                    <button
                      v-for="(layout, index) in layouts"
                      :key="layout.id"
                      type="button"
                      class="rounded-md border px-3 py-1 text-xs transition hover:bg-muted"
                      :class="index === layoutIndex ? 'border-primary bg-primary/5 text-primary' : 'border-border text-muted-foreground'"
                      @click="selectLayout(index)"
                    >
                      {{ layout.title || layout.id }}
                    </button>
                  </div>
                </div>

                <div v-if="layouts.length" class="space-y-3">
                  <div class="rounded-lg border bg-white p-4 shadow-sm">
                    <img
                      v-if="activeLayout?.url"
                      :src="activeLayout.url"
                      :alt="activeLayout?.title || 'PCB layout'"
                      class="mx-auto max-h-[520px] w-full max-w-full object-contain"
                    />
                  </div>
                  <div class="flex items-center justify-between text-sm text-muted-foreground">
                    <div class="space-x-2">
                      <span class="font-medium text-foreground">{{ activeLayout?.title ?? "Layout" }}</span>
                      <span v-if="activeLayout?.layers?.length">
                        Layers: {{ activeLayout.layers.join(", ") }}
                      </span>
                    </div>
                    <a
                      v-if="activeLayout?.url"
                      :href="activeLayout.url"
                      target="_blank"
                      rel="noopener"
                      class="underline"
                    >
                      Open full size
                    </a>
                  </div>
                </div>
                <p v-else class="text-sm text-muted-foreground">No layout previews available.</p>
              </section>

              <section class="space-y-3">
                <h3 class="text-sm font-medium text-muted-foreground">3D view</h3>
                <ul v-if="models.length" class="space-y-2 text-sm">
                  <li v-for="model in models" :key="model.id" class="flex items-center gap-2">
                    <a v-if="model.url" :href="model.url" target="_blank" rel="noopener" class="underline">
                      Download {{ model.title || model.filename }}
                    </a>
                    <span v-else class="text-muted-foreground">{{ model.title || model.filename }} unavailable</span>
                    <span class="text-muted-foreground">(.glb)</span>
                  </li>
                </ul>
                <p v-else class="text-sm text-muted-foreground">No 3D models generated.</p>
              </section>

              <section v-if="metadataEntries.length" class="space-y-3">
                <h3 class="text-sm font-medium text-muted-foreground">KiCad metadata</h3>
                <div class="overflow-hidden rounded-md border">
                  <dl class="grid gap-2 bg-muted/40 p-4 text-sm text-muted-foreground">
                    <template v-for="[key, value] in metadataEntries" :key="key">
                      <dt class="font-medium capitalize text-foreground">{{ key.replace(/_/g, " ") }}</dt>
                      <dd>{{ value as string }}</dd>
                    </template>
                  </dl>
                </div>
              </section>
            </div>
          </CardContent>
        </Card>

        <Card class="lg:col-span-2">
          <CardHeader>
            <CardTitle>Uploaded files</CardTitle>
            <CardDescription>
              Files associated with this project.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div v-if="project.files.length === 0"
              class="rounded-md border border-dashed border-muted-foreground/40 p-6 text-center text-sm text-muted-foreground">
              No files uploaded yet.
            </div>
            <div v-else class="overflow-x-auto">
              <table class="w-full min-w-[560px] text-left text-sm">
                <thead class="border-b border-border text-muted-foreground">
                  <tr class="h-10">
                    <th class="px-3 font-medium">Filename</th>
                    <th class="px-3 font-medium">Type</th>
                    <th class="px-3 font-medium">Stored at</th>
                    <th class="px-3 font-medium">Uploaded</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="file in project.files" :key="file.id" class="border-b border-border/60 last:border-0">
                    <td class="px-3 py-3 font-medium text-foreground">{{ file.filename }}</td>
                    <td class="px-3 py-3 capitalize">{{ file.file_type ?? "unknown" }}</td>
                    <td class="px-3 py-3 text-xs text-muted-foreground break-all">{{ file.storage_path }}</td>
                    <td class="px-3 py-3 text-muted-foreground">{{ formatDateTime(file.created_at) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>
