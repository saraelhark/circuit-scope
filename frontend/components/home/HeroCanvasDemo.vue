<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import CommentIcon from '~/components/projects/CommentIcon.vue'

type Phase
  = 'idle'
    | 'cursor-enter'
    | 'cursor-move'
    | 'cursor-click'
    | 'pin-place'
    | 'pin-settle'
    | 'preview-show'
    | 'interactive'
    | 'fade-out'

const phase = ref<Phase>('idle')
const showPreview = ref(false)
const containerRef = ref<HTMLElement | null>(null)
const reducedMotion = ref(false)
const isVisible = ref(false)
let observer: IntersectionObserver | null = null
let timeouts: ReturnType<typeof setTimeout>[] = []
let animationStopped = false
let interactiveTimeout: ReturnType<typeof setTimeout> | null = null

// Pin target position (percentage of container)
const pinX = 62
const pinY = 42

// Cursor position tracks animation
const cursorX = ref(10)
const cursorY = ref(12)
const cursorVisible = ref(false)
const cursorPressed = ref(false)
const showRipple = ref(false)
const pinVisible = ref(false)
const fadeOut = ref(false)

function clearAllTimeouts() {
  timeouts.forEach(clearTimeout)
  timeouts = []
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    timeouts.push(setTimeout(resolve, ms))
  })
}

function resetState() {
  clearAllTimeouts()
  phase.value = 'idle'
  cursorVisible.value = false
  cursorPressed.value = false
  showRipple.value = false
  pinVisible.value = false
  showPreview.value = false
  fadeOut.value = false
  cursorX.value = 10
  cursorY.value = 12
}

async function runAnimation() {
  // Reset state
  resetState()
  animationStopped = false

  if (reducedMotion.value) {
    pinVisible.value = true
    showPreview.value = true
    phase.value = 'preview-show'
    return
  }

  // idle
  await delay(1500)
  if (animationStopped) return

  // cursor-enter
  phase.value = 'cursor-enter'
  cursorVisible.value = true
  await delay(600)
  if (animationStopped) return

  // cursor-move
  phase.value = 'cursor-move'
  cursorX.value = pinX
  cursorY.value = pinY
  await delay(1200)
  if (animationStopped) return

  // cursor-click
  phase.value = 'cursor-click'
  cursorPressed.value = true
  showRipple.value = true
  await delay(300)
  if (animationStopped) return

  // pin-place
  phase.value = 'pin-place'
  pinVisible.value = true
  cursorVisible.value = false
  cursorPressed.value = false
  await delay(500)
  if (animationStopped) return

  // pin-settle
  phase.value = 'pin-settle'
  showRipple.value = false
  await delay(800)
  if (animationStopped) return

  // preview-show
  phase.value = 'preview-show'
  showPreview.value = true
  await delay(2500)
  if (animationStopped) return

  // interactive — user can hover pin to toggle preview
  phase.value = 'interactive'
  showPreview.value = false
  scheduleResume()
}

function scheduleResume() {
  if (interactiveTimeout) clearTimeout(interactiveTimeout)
  interactiveTimeout = setTimeout(() => {
    if (animationStopped || phase.value !== 'interactive') return
    fadeAndLoop()
  }, 5000)
}

async function fadeAndLoop() {
  // fade-out
  phase.value = 'fade-out'
  fadeOut.value = true
  await delay(800)
  if (animationStopped) return

  // Pause between loops
  resetState()
  await delay(1500)
  if (animationStopped) return

  // Loop if still visible
  if (isVisible.value) {
    runAnimation()
  }
}

function handlePinEnter() {
  if (phase.value !== 'interactive') return
  showPreview.value = true
  // Pause the auto-resume while user is hovering
  if (interactiveTimeout) clearTimeout(interactiveTimeout)
}

function handlePinLeave() {
  if (phase.value !== 'interactive') return
  showPreview.value = false
  // Restart the auto-resume countdown
  scheduleResume()
}

function stopAnimation() {
  animationStopped = true
  if (interactiveTimeout) clearTimeout(interactiveTimeout)
  resetState()
}

onMounted(async () => {
  reducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  await nextTick()

  observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (!entry) return

      if (entry.isIntersecting) {
        isVisible.value = true
        runAnimation()
      }
      else {
        isVisible.value = false
        stopAnimation()
      }
    },
    { threshold: 0.3 },
  )

  if (containerRef.value) {
    observer.observe(containerRef.value)
  }
})

onUnmounted(() => {
  clearAllTimeouts()
  if (interactiveTimeout) clearTimeout(interactiveTimeout)
  observer?.disconnect()
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative w-full aspect-[3/2] max-w-[520px] rounded-xl overflow-hidden bg-white border border-gray-200 select-none"
    aria-label="Animated demo showing collaborative design review on a circuit schematic"
  >
    <!-- Dot grid background -->
    <svg
      class="absolute inset-0 w-full h-full"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <pattern
          id="hero-dot-grid"
          x="0"
          y="0"
          width="20"
          height="20"
          patternUnits="userSpaceOnUse"
        >
          <circle
            cx="10"
            cy="10"
            r="0.8"
            fill="#D1D5DB"
          />
        </pattern>
      </defs>
      <rect
        width="100%"
        height="100%"
        fill="url(#hero-dot-grid)"
      />
    </svg>

    <!-- Schematic SVG -->
    <svg
      class="absolute inset-0 w-full h-full"
      viewBox="0 0 520 347"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- Power rail lines -->
      <line
        x1="40"
        y1="80"
        x2="480"
        y2="80"
        stroke="#D1D5DB"
        stroke-width="1"
        stroke-dasharray="4 4"
      />
      <line
        x1="40"
        y1="270"
        x2="480"
        y2="270"
        stroke="#D1D5DB"
        stroke-width="1"
        stroke-dasharray="4 4"
      />

      <!-- VIN label -->
      <text
        x="50"
        y="120"
        fill="#15803D"
        font-family="'JetBrains Mono', monospace"
        font-size="11"
        font-weight="600"
      >VIN</text>

      <!-- Input trace (horizontal) -->
      <line
        x1="80"
        y1="140"
        x2="160"
        y2="140"
        stroke="#2FA37A"
        stroke-width="2"
      />

      <!-- Input capacitor C1 -->
      <rect
        x="100"
        y="155"
        width="24"
        height="44"
        rx="3"
        stroke="#0D9488"
        stroke-width="1.5"
        fill="none"
      />
      <line
        x1="112"
        y1="140"
        x2="112"
        y2="155"
        stroke="#2FA37A"
        stroke-width="2"
      />
      <line
        x1="112"
        y1="199"
        x2="112"
        y2="220"
        stroke="#2FA37A"
        stroke-width="2"
      />
      <text
        x="88"
        y="185"
        fill="#374151"
        font-family="'JetBrains Mono', monospace"
        font-size="9"
        text-anchor="end"
      >C1</text>
      <text
        x="88"
        y="196"
        fill="#0D9488"
        font-family="'JetBrains Mono', monospace"
        font-size="8"
        text-anchor="end"
      >4.7uF</text>

      <!-- Voltage regulator IC -->
      <rect
        x="180"
        y="115"
        width="100"
        height="70"
        rx="4"
        stroke="#0D9488"
        stroke-width="2"
        fill="#F9FAFB"
      />
      <text
        x="230"
        y="145"
        fill="#1F2937"
        font-family="'JetBrains Mono', monospace"
        font-size="11"
        text-anchor="middle"
        font-weight="600"
      >LM1117</text>
      <text
        x="230"
        y="160"
        fill="#0D9488"
        font-family="'JetBrains Mono', monospace"
        font-size="9"
        text-anchor="middle"
      >3.3V</text>

      <!-- IC pin labels -->
      <text
        x="174"
        y="143"
        fill="#374151"
        font-family="'JetBrains Mono', monospace"
        font-size="8"
        text-anchor="end"
      >IN</text>
      <text
        x="286"
        y="143"
        fill="#374151"
        font-family="'JetBrains Mono', monospace"
        font-size="8"
      >OUT</text>
      <text
        x="230"
        y="198"
        fill="#374151"
        font-family="'JetBrains Mono', monospace"
        font-size="8"
        text-anchor="middle"
      >GND</text>

      <!-- IC to input trace -->
      <line
        x1="160"
        y1="140"
        x2="180"
        y2="140"
        stroke="#2FA37A"
        stroke-width="2"
      />

      <!-- IC to output trace -->
      <line
        x1="280"
        y1="140"
        x2="380"
        y2="140"
        stroke="#2FA37A"
        stroke-width="2"
      />

      <!-- GND trace from IC -->
      <line
        x1="230"
        y1="185"
        x2="230"
        y2="220"
        stroke="#2FA37A"
        stroke-width="2"
      />

      <!-- Output capacitor C2 -->
      <rect
        x="340"
        y="155"
        width="24"
        height="44"
        rx="3"
        stroke="#0D9488"
        stroke-width="1.5"
        fill="none"
      />
      <line
        x1="352"
        y1="140"
        x2="352"
        y2="155"
        stroke="#2FA37A"
        stroke-width="2"
      />
      <line
        x1="352"
        y1="199"
        x2="352"
        y2="220"
        stroke="#2FA37A"
        stroke-width="2"
      />
      <text
        x="374"
        y="175"
        fill="#374151"
        font-family="'JetBrains Mono', monospace"
        font-size="9"
      >C2</text>
      <text
        x="374"
        y="186"
        fill="#0D9488"
        font-family="'JetBrains Mono', monospace"
        font-size="8"
      >4.7uF</text>

      <!-- VOUT label -->
      <text
        x="400"
        y="134"
        fill="#15803D"
        font-family="'JetBrains Mono', monospace"
        font-size="11"
        font-weight="600"
      >VOUT</text>

      <!-- Output continuation trace -->
      <line
        x1="380"
        y1="140"
        x2="440"
        y2="140"
        stroke="#2FA37A"
        stroke-width="2"
      />

      <!-- GND bus -->
      <line
        x1="112"
        y1="220"
        x2="352"
        y2="220"
        stroke="#2FA37A"
        stroke-width="2"
      />

      <!-- GND symbol -->
      <line
        x1="220"
        y1="220"
        x2="240"
        y2="220"
        stroke="#6B7280"
        stroke-width="2"
      />
      <line
        x1="216"
        y1="228"
        x2="244"
        y2="228"
        stroke="#6B7280"
        stroke-width="1.5"
      />
      <line
        x1="222"
        y1="234"
        x2="238"
        y2="234"
        stroke="#6B7280"
        stroke-width="1"
      />
      <line
        x1="227"
        y1="240"
        x2="233"
        y2="240"
        stroke="#6B7280"
        stroke-width="0.5"
      />
      <text
        x="230"
        y="255"
        fill="#374151"
        font-family="'JetBrains Mono', monospace"
        font-size="9"
        text-anchor="middle"
      >GND</text>

      <!-- Decoupling cap C3 near output -->
      <rect
        x="420"
        y="155"
        width="20"
        height="36"
        rx="2"
        stroke="#0D9488"
        stroke-width="1"
        fill="none"
      />
      <line
        x1="430"
        y1="140"
        x2="430"
        y2="155"
        stroke="#2FA37A"
        stroke-width="1.5"
      />
      <line
        x1="430"
        y1="191"
        x2="430"
        y2="220"
        stroke="#2FA37A"
        stroke-width="1.5"
      />
      <line
        x1="352"
        y1="220"
        x2="430"
        y2="220"
        stroke="#2FA37A"
        stroke-width="2"
      />
      <text
        x="450"
        y="172"
        fill="#374151"
        font-family="'JetBrains Mono', monospace"
        font-size="8"
      >C3</text>
      <text
        x="450"
        y="183"
        fill="#0D9488"
        font-family="'JetBrains Mono', monospace"
        font-size="7"
      >100nF</text>

      <!-- Junction dots -->
      <circle
        cx="112"
        cy="140"
        r="3"
        fill="#2FA37A"
      />
      <circle
        cx="352"
        cy="140"
        r="3"
        fill="#2FA37A"
      />
      <circle
        cx="430"
        cy="140"
        r="3"
        fill="#2FA37A"
      />
      <circle
        cx="230"
        cy="220"
        r="3"
        fill="#2FA37A"
      />
      <circle
        cx="352"
        cy="220"
        r="3"
        fill="#2FA37A"
      />

      <!-- Title block -->
      <rect
        x="330"
        y="290"
        width="170"
        height="40"
        rx="2"
        stroke="#D1D5DB"
        stroke-width="1"
        fill="none"
      />
      <text
        x="415"
        y="308"
        fill="#1F2937"
        font-family="'JetBrains Mono', monospace"
        font-size="9"
        text-anchor="middle"
        font-weight="600"
      >PSU_3V3_REG</text>
      <text
        x="415"
        y="322"
        fill="#6B7280"
        font-family="'JetBrains Mono', monospace"
        font-size="7"
        text-anchor="middle"
      >Sheet 1/3 | Rev B</text>
    </svg>

    <!-- Animated cursor -->
    <div
      class="absolute pointer-events-none z-30 transition-opacity duration-500"
      :class="cursorVisible ? 'opacity-100' : 'opacity-0'"
      :style="{
        left: `${cursorX}%`,
        top: `${cursorY}%`,
        transition: phase === 'cursor-move'
          ? 'left 1.2s cubic-bezier(0.4, 0, 0.2, 1), top 1.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.5s'
          : 'opacity 0.5s',
      }"
    >
      <svg
        width="20"
        height="24"
        viewBox="0 0 20 24"
        fill="none"
        class="drop-shadow-lg transition-transform duration-150"
        :class="cursorPressed ? 'scale-90' : ''"
      >
        <path
          d="M3 1L3 17L7.5 13L12.5 21L15 19.5L10 12L16 11L3 1Z"
          fill="white"
          stroke="#1E2A27"
          stroke-width="1.5"
          stroke-linejoin="round"
        />
      </svg>
    </div>

    <!-- Click ripple -->
    <div
      v-if="showRipple"
      class="absolute pointer-events-none z-20"
      :style="{ left: `${pinX}%`, top: `${pinY}%`, transform: 'translate(-50%, -50%)' }"
    >
      <div class="hero-ripple" />
    </div>

    <!-- Comment pin + preview card -->
    <div
      class="absolute z-40 transition-all"
      :class="[
        pinVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-0',
        fadeOut ? 'hero-fade-out' : '',
        phase === 'interactive' ? 'cursor-pointer' : 'pointer-events-none',
      ]"
      :style="{
        left: `${pinX}%`,
        top: `${pinY}%`,
        transform: 'translate(-50%, -100%)',
        transition: fadeOut
          ? 'opacity 0.8s ease-out'
          : 'opacity 0.4s, transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }"
      @mouseenter="handlePinEnter"
      @mouseleave="handlePinLeave"
    >
      <CommentIcon
        initial="A"
        size="md"
        color="#FFD02B"
      />

      <!-- Preview card (positioned to the left of pin) -->
      <Transition name="hero-preview">
        <div
          v-if="showPreview"
          class="absolute right-full top-1/2 -translate-y-1/2 mr-2 w-[200px] rounded-lg bg-white shadow-lg border border-gray-100 p-2.5 pointer-events-none"
        >
          <div class="flex items-center gap-1.5 mb-1">
            <div class="h-5 w-5 rounded-full bg-[#60A5FA] flex items-center justify-center text-[10px] font-bold text-white">
              A
            </div>
            <span class="text-xs font-semibold text-gray-800">Alex M.</span>
          </div>
          <p class="text-[11px] text-gray-600 leading-snug">
            Is the input cap value correct for this regulator?
          </p>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.hero-ripple {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #FFD02B;
  animation: hero-ripple-expand 0.6s ease-out forwards;
  transform: translate(-50%, -50%);
}

@keyframes hero-ripple-expand {
  0% {
    width: 0;
    height: 0;
    opacity: 1;
  }
  100% {
    width: 50px;
    height: 50px;
    opacity: 0;
  }
}

.hero-fade-out {
  opacity: 0 !important;
}

.hero-preview-enter-active {
  transition: opacity 0.2s, transform 0.2s;
}
.hero-preview-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.hero-preview-enter-from,
.hero-preview-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(4px);
}
</style>
