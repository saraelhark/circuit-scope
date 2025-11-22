<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import * as THREE from "three"
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js"

const props = withDefaults(
  defineProps<{
    modelUrl?: string
    interactionEnabled?: boolean
  }>(),
  {
    modelUrl: undefined,
    interactionEnabled: true,
  },
)

const emit = defineEmits<{
  (e: "loaded"): void
  (e: "error", message: string): void
  (e: "bounds-change", rect: DOMRect): void
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let frameId: number | null = null
let currentModel: THREE.Object3D | null = null
let resizeObserver: ResizeObserver | null = null
let currentOrientation: "front" | "back" = "front"
let cameraDistance = 6

function initScene() {
  if (!containerRef.value || renderer) return

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.shadowMap.enabled = false
  renderer.setPixelRatio(globalThis.devicePixelRatio ?? 1)

  containerRef.value.appendChild(renderer.domElement)

  scene = new THREE.Scene()
  scene.background = new THREE.Color("#05060a")

  camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100)
  camera.position.set(0, 0, cameraDistance)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.enablePan = false

  const ambient = new THREE.AmbientLight(0xffffff, 0.8)
  scene.add(ambient)

  scene.add(camera)

  const mainLight = new THREE.DirectionalLight(0xffffff, 0.9)
  mainLight.position.set(5, 5, 5)
  mainLight.target.position.set(0, 0, -1)
  camera.add(mainLight)
  camera.add(mainLight.target)

  const fillLight = new THREE.DirectionalLight(0x7cffe8, 0.5)
  fillLight.position.set(-5, -5, 5)
  fillLight.target.position.set(0, 0, -1)
  camera.add(fillLight)
  camera.add(fillLight.target)

  startRenderingLoop()
  updateSize()
}

function startRenderingLoop() {
  const animate = () => {
    controls?.update()
    if (renderer && scene && camera) {
      renderer.render(scene, camera)
    }
    frameId = globalThis.requestAnimationFrame(animate)
  }
  frameId = globalThis.requestAnimationFrame(animate)
}

function stopRenderingLoop() {
  if (frameId !== null) {
    globalThis.cancelAnimationFrame(frameId)
    frameId = null
  }
}

function disposeModel() {
  if (currentModel && scene) {
    scene.remove(currentModel)
    currentModel.traverse((child: THREE.Object3D) => {
      const mesh = child as THREE.Mesh
      if (mesh.geometry) {
        mesh.geometry.dispose()
      }
      const material = mesh.material as THREE.Material | THREE.Material[] | undefined
      if (Array.isArray(material)) {
        material.forEach((mat) => mat.dispose())
      } else {
        material?.dispose()
      }
    })
  }
  currentModel = null
}

function dispose() {
  stopRenderingLoop()
  disposeModel()
  controls?.dispose()
  controls = null
  renderer?.dispose()
  if (renderer?.domElement && renderer.domElement.parentElement) {
    renderer.domElement.parentElement.removeChild(renderer.domElement)
  }
  renderer = null
  scene = null
  camera = null
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
}

function loadModel(url?: string) {
  if (!scene) return
  if (!url) {
    disposeModel()
    isLoading.value = false
    return
  }
  isLoading.value = true
  errorMessage.value = null

  disposeModel()

  const loader = new GLTFLoader()
  loader.load(
    url,
    (gltf: GLTF) => {
      if (!scene) return
      const root = new THREE.Group()

      const box = new THREE.Box3().setFromObject(gltf.scene)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())

      gltf.scene.position.sub(center)
      root.add(gltf.scene)

      root.rotation.x = Math.PI / 2

      const maxDimension = Math.max(size.x, size.y, size.z) || 1
      const desiredSize = 4
      const scale = desiredSize / maxDimension
      root.scale.setScalar(scale)

      currentModel = root
      scene.add(root)

      if (camera && controls) {
        const fill = 0.7
        const fov = (camera.fov * Math.PI) / 180
        const displayHeight = Math.max(size.x, size.z)
        const halfHeight = (displayHeight * scale) / 2
        cameraDistance = halfHeight / (Math.tan(fov / 2) * fill)

        cameraDistance = Math.max(cameraDistance, 2)

        camera.near = cameraDistance / 50
        camera.far = cameraDistance * 50
        camera.updateProjectionMatrix()
      }

      setOrientation(currentOrientation)

      isLoading.value = false
      emit("loaded")
      nextTick(updateBounds)
    },
    undefined,
    (error: unknown) => {
      console.error("Failed to load GLB", error)
      isLoading.value = false
      errorMessage.value = "Failed to load 3D preview"
      emit("error", errorMessage.value)
    },
  )
}

function updateSize() {
  if (!containerRef.value || !renderer || !camera) return

  const { clientWidth, clientHeight } = containerRef.value
  renderer.setSize(clientWidth, clientHeight)
  camera.aspect = clientWidth / Math.max(clientHeight, 1)
  camera.updateProjectionMatrix()
  updateBounds()
}

function updateBounds() {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  emit("bounds-change", rect)
}

function setOrientation(target: "front" | "back") {
  if (!camera || !controls) return
  const z = target === "front" ? cameraDistance : -cameraDistance
  camera.position.set(0, 0, z)
  controls.target.set(0, 0, 0)
  controls.update()
  currentOrientation = target
}

function toggleFlip() {
  setOrientation(currentOrientation === "front" ? "back" : "front")
}

defineExpose({
  setOrientation,
  toggleFlip,
  updateBounds,
})

watch(
  () => props.modelUrl,
  (url) => {
    loadModel(url)
  },
)

watch(
  () => props.interactionEnabled,
  (enabled) => {
    if (controls) {
      controls.enabled = enabled
    }
  },
  { immediate: true },
)

onMounted(() => {
  initScene()
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => updateSize())
    resizeObserver.observe(containerRef.value)
  }
  loadModel(props.modelUrl)
  nextTick(updateBounds)
})

onBeforeUnmount(() => {
  dispose()
})
</script>

<template>
  <div ref="containerRef" class="relative h-full w-full overflow-hidden rounded-lg bg-[#05060a]">
    <div v-if="!modelUrl" class="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">
      No 3D model preview available.
    </div>
    <div v-else-if="errorMessage"
      class="absolute inset-0 flex items-center justify-center bg-background/70 text-sm text-destructive">
      {{ errorMessage }}
    </div>
    <div v-else-if="isLoading"
      class="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">
      Loading 3D preview…
    </div>
  </div>
</template>
