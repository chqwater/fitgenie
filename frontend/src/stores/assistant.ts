import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AssistantDirectives, CheckinResponse } from '@/api/types'

export const useAssistantStore = defineStore('assistant', () => {
  // 当日已生成的计划（供小助手上下文使用）
  const currentPlan = ref<CheckinResponse | null>(null)

  // 小助手记录的待应用指令
  const pendingDirectives = ref<AssistantDirectives | null>(null)

  function setCurrentPlan(plan: CheckinResponse | null) {
    currentPlan.value = plan
  }

  function setPendingDirectives(d: AssistantDirectives | null) {
    pendingDirectives.value = d
  }

  function clearDirectives() {
    pendingDirectives.value = null
  }

  return { currentPlan, pendingDirectives, setCurrentPlan, setPendingDirectives, clearDirectives }
})
