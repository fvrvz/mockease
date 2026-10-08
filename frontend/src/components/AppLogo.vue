<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: number
    rounded?: boolean
  }>(),
  {
    size: 28,
    rounded: true,
  }
)
</script>

<template>
  <div
    class="brand-logo"
    :style="{
      width: `${size}px`,
      height: `${size}px`,
      borderRadius: rounded ? `${Math.round(size * 0.28)}px` : '4px',
    }"
  >
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#8B5CF6" />
          <stop offset="100%" stop-color="#6366F1" />
        </linearGradient>
        <radialGradient id="dotGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#FFFFFF" />
          <stop offset="100%" stop-color="#E0E7FF" />
        </radialGradient>
      </defs>

      <!-- Background Plate -->
      <rect
        width="32"
        height="32"
        rx="8"
        fill="#13131A"
      />
      <rect
        x="0.75"
        y="0.75"
        width="30.5"
        height="30.5"
        rx="7.25"
        stroke="url(#logoGrad)"
        stroke-width="1.5"
        stroke-opacity="0.8"
      />

      <!-- Puzzle Piece Emblem -->
      <path
        d="M10 8h4v3a2 2 0 0 0 4 0V8h4a2 2 0 0 1 2 2v4h-3a2 2 0 0 0 0 4h3v4a2 2 0 0 1-2 2h-4v-3a2 2 0 0 0-4 0v3h-4a2 2 0 0 1-2-2v-4h3a2 2 0 0 0 0-4h-3v-4a2 2 0 0 1 2-2z"
        fill="url(#logoGrad)"
      />

      <!-- Core Dot -->
      <circle cx="16" cy="16" r="2.2" fill="url(#dotGlow)" />
    </svg>
  </div>
</template>

<style scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
}

.brand-logo:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 18px rgba(139, 92, 246, 0.4);
}

.brand-logo svg {
  display: block;
}
</style>
