<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>

  <!-- 全局小助手面板（只在登录状态下显示） -->
  <AssistantPanel
    v-if="isLoggedIn"
    :current-plan="currentPlan ? (currentPlan as unknown as Record<string, unknown>) : null"
    @directives-updated="onDirectivesUpdated"
  />

  <!-- 全局页脚 -->
  <footer class="app-footer">
    © {{ year }} FitGenie · 陈浩泉 Haoquan Chen · MSc, Imperial College London
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AssistantPanel from '@/components/AssistantPanel.vue'
import { useAssistantStore } from '@/stores/assistant'
import type { AssistantDirectives } from '@/api/types'

const assistantStore = useAssistantStore()
const currentPlan = computed(() => assistantStore.currentPlan)
const isLoggedIn = computed(() => !!localStorage.getItem('token'))
const year = new Date().getFullYear()

function onDirectivesUpdated(d: AssistantDirectives) {
  assistantStore.setPendingDirectives(d)
}
</script>

<style scoped>
.app-footer {
  text-align: center;
  padding: 20px 16px 24px;
  font-size: 12px;
  color: var(--text-muted, #a0aec0);
  letter-spacing: 0.04em;
  background: transparent;
  position: relative;
  z-index: 10;
}

@media (max-width: 480px) {
  .app-footer {
    font-size: 11px;
    padding: 16px 12px 20px;
  }
}
</style>
