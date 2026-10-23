<script setup lang="ts">
defineProps<{ title: string; description: string; eyebrow?: string }>()
</script>

<template>
  <header class="page-heading">
    <div>
      <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
      <h1 id="page-heading" tabindex="-1">{{ title }}</h1>
      <p class="page-description">{{ description }}</p>
    </div>
    <slot />
  </header>
</template>
