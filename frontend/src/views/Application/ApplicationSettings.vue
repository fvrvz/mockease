<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="settings-view">
    <h1 style="color: #e8e8f0;">Application Settings</h1>
    <p style="color: #6666a0;">Settings for application: {{ route.params.id }}</p>
    <p style="color: #6666a0;">Phase 5 will complete this view.</p>
  </div>
</template>

<style scoped>
.settings-view {
  padding: 2rem;
}
</style>
