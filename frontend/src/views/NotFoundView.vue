<script setup lang="ts">
import PageHeading from '../components/PageHeading.vue'
import DataState from '../components/DataState.vue'
</script>

<template>
  <PageHeading title="页面不存在" description="检查访问地址，或返回工作台继续。" />
  <section class="surface"><DataState kind="empty" title="没有找到这个页面" description="这个地址可能已经变更。"><RouterLink class="text-link" to="/">返回工作台 →</RouterLink></DataState></section>
</template>
