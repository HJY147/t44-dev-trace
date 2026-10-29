<script setup lang="ts">
import { ref } from 'vue'
import { ElButton } from 'element-plus'
import { api, request } from '../api'
import { asRow } from '../contract'
import { bootstrap, workspace } from '../workspace'
import { useRequestState } from '../useRequestState'
const username = ref('')
const password = ref('')
const { busy, failure: error, isActive } = useRequestState<string>()
async function login(): Promise<void> {
  if (!isActive() || busy.value) return
  if (!username.value || !password.value) { error.value = '请填写账号和密码。'; return }
  busy.value = true; error.value = ''
  let token = api.token
  try {
    const result = asRow((await request('login', {}, {}, { username: username.value, password: password.value })).data)
    if (!isActive() || api.token !== token) return
    api.token = token = String(result.access_token)
    await bootstrap()
    if (api.token === token) workspace.notice = '已登录，工作空间已同步。'
  } catch (cause) { if (!isActive() || api.token !== token) return; api.token = ''; error.value = cause instanceof Error ? cause.message : '登录暂未完成，请稍后再试。' }
  finally { password.value = ''; busy.value = false }
}
</script>

<template>
  <section class="login-page" aria-label="登录留痕">
    <div class="login-layout">
      <div class="login-story">
        <div class="brand"><img src="/favicon.svg" width="42" height="42" alt="" /><span><strong>留痕</strong><small>研发交付工作空间</small></span></div>
        <h2>让每次交付，<br />都有迹可循。</h2>
        <p>从一个计划，到一次可靠的发布。<br />在这里，把进度、依据和团队的决定连接起来。</p>
        <div class="login-story__note"><small>A CLEAR PATH TO DELIVERY</small><p>计划有安排，推进有依据</p><div class="login-story__steps"><span>登记任务</span><span aria-hidden="true">→</span><span>协作评审</span><span aria-hidden="true">→</span><span>交付留痕</span></div></div>
      </div>
    <form class="login-card" @submit.prevent="login">
      <h1>登录工作空间</h1><p>使用已开通的团队账号，继续你的交付工作。</p>
      <div v-if="workspace.notice" class="inline-notice">{{ workspace.notice }}</div>
      <label for="login-username">账号</label><input id="login-username" v-model="username" autocomplete="username" maxlength="64" autofocus :disabled="busy" />
      <label for="login-password">密码</label><input id="login-password" v-model="password" type="password" autocomplete="off" maxlength="128" :disabled="busy" />
      <p v-if="error" class="field-error" role="alert">{{ error }}</p>
      <ElButton type="primary" native-type="submit" :loading="busy" class="login-submit">登录</ElButton><small>账号由团队管理员开通。仅可访问你参与的项目。</small>
    </form>
    </div>
  </section>
</template>
