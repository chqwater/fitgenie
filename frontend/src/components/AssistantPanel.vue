<template>
  <!-- 浮动按钮 -->
  <div class="assistant-fab" @click="toggle" :class="{ open: isOpen }">
    <span class="fab-icon">{{ isOpen ? '✕' : '🤖' }}</span>
    <span v-if="!isOpen && unreadBadge" class="fab-badge">{{ unreadBadge }}</span>
  </div>

  <!-- 面板 -->
  <transition name="panel-slide">
    <div v-if="isOpen" class="assistant-panel">
      <div class="panel-header">
        <div class="panel-title">
          <span class="panel-icon">🤖</span>
          <div>
            <div class="panel-name">FitGenie 小助手</div>
            <div class="panel-sub">随时告诉我你的想法</div>
          </div>
        </div>
        <div class="panel-actions">
          <span
            v-if="hasPendingDirectives"
            class="directive-badge"
            title="已有待应用的调整指令"
          >有调整意见</span>
          <button class="panel-close" @click="toggle">✕</button>
        </div>
      </div>

      <!-- 偏好标签 -->
      <div v-if="preferenceTags.length" class="pref-tags">
        <span class="pref-label">已记录偏好：</span>
        <span v-for="tag in preferenceTags" :key="tag" class="pref-tag">{{ tag }}</span>
      </div>

      <!-- 对话记录 -->
      <div class="chat-messages" ref="messagesList">
        <div v-if="messages.length === 0" class="chat-empty">
          <p>你好！我是你的 FitGenie 小助手 👋</p>
          <p>你可以告诉我你的喜好、身体状况，或者对今日计划的想法，我会帮你定制更适合你的方案。</p>
        </div>

        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="message"
          :class="msg.role"
        >
          <div class="message-bubble">{{ msg.content }}</div>
          <div v-if="msg.directives" class="directive-hint">
            <span class="directive-icon">⚡</span>
            已记录调整指令，点击"重新生成计划"应用
          </div>
        </div>

        <div v-if="thinking" class="message assistant">
          <div class="message-bubble thinking">
            <span class="dot" /><span class="dot" /><span class="dot" />
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="chat-input-area">
        <textarea
          v-model="inputText"
          class="chat-input"
          placeholder="说说你的想法..."
          rows="2"
          @keydown.enter.exact.prevent="send"
        />
        <button class="send-btn" :disabled="!inputText.trim() || thinking" @click="send">
          发送
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { assistantApi } from '@/api'
import type { AssistantDirectives, AssistantHistoryItem } from '@/api/types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  directives?: AssistantDirectives | null
}

const props = defineProps<{
  currentPlan?: Record<string, unknown> | null
}>()

const emit = defineEmits<{
  (e: 'directives-updated', d: AssistantDirectives): void
}>()

const isOpen = ref(false)
const inputText = ref('')
const thinking = ref(false)
const messages = ref<Message[]>([])
const messagesList = ref<HTMLElement | null>(null)
const unreadBadge = ref(0)
const pendingDirectives = ref<AssistantDirectives | null>(null)
const preferences = ref<Record<string, string>>({})

const hasPendingDirectives = computed(() => !!pendingDirectives.value)

const preferenceTags = computed(() => {
  const prefs = preferences.value
  const tags: string[] = []
  if (prefs.workout_likes) tags.push(`💪 ${prefs.workout_likes}`)
  if (prefs.workout_dislikes) tags.push(`🚫 避免：${prefs.workout_dislikes}`)
  if (prefs.diet_restrictions) tags.push(`🥗 ${prefs.diet_restrictions}`)
  if (prefs.injury_notes) tags.push(`⚠️ ${prefs.injury_notes}`)
  return tags.slice(0, 3)
})

function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    unreadBadge.value = 0
    nextTick(() => scrollToBottom())
  }
}

async function send() {
  const text = inputText.value.trim()
  if (!text || thinking.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  thinking.value = true
  await nextTick()
  scrollToBottom()

  try {
    const res = await assistantApi.chat({
      message: text,
      current_plan: props.currentPlan ?? null,
    })
    const { reply, directives, preferences_updated } = res.data

    messages.value.push({
      role: 'assistant',
      content: reply,
      directives: directives ?? null,
    })

    if (directives && Object.keys(directives).length > 0) {
      pendingDirectives.value = directives
      emit('directives-updated', directives)
    }

    if (preferences_updated) {
      await loadPreferences()
    }
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，我暂时无法回应，请稍后再试。',
    })
  } finally {
    thinking.value = false
    if (!isOpen.value) unreadBadge.value++
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesList.value) {
    messagesList.value.scrollTop = messagesList.value.scrollHeight
  }
}

async function loadHistory() {
  try {
    const res = await assistantApi.history(20)
    messages.value = res.data.map((item: AssistantHistoryItem) => ({
      role: item.role as 'user' | 'assistant',
      content: item.content,
    }))
    await nextTick()
    scrollToBottom()
  } catch {
    // 静默失败
  }
}

async function loadPreferences() {
  try {
    const res = await assistantApi.preferences()
    preferences.value = res.data ?? {}
  } catch {
    // 静默失败
  }
}

// 向外暴露待应用指令（供 CheckinView 使用）
function getDirectives() {
  return pendingDirectives.value
}

function clearDirectives() {
  pendingDirectives.value = null
}

defineExpose({ getDirectives, clearDirectives, toggle })

onMounted(async () => {
  await Promise.all([loadHistory(), loadPreferences()])
})

// 计划变化时让助手知晓
watch(() => props.currentPlan, (plan) => {
  if (plan && isOpen.value) {
    // 不自动发消息，只是让下次对话带上 context
  }
})
</script>

<style scoped>
/* ── 浮动按钮 ── */
.assistant-fab {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5ea282, #f07c5a);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(94,162,130,0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
}
.assistant-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(94,162,130,0.5);
}
.assistant-fab.open {
  transform: scale(0.95);
}
.fab-icon { font-size: 22px; }
.fab-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #f07c5a;
  color: white;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

/* ── 面板 ── */
.assistant-panel {
  position: fixed;
  bottom: 100px;
  right: 32px;
  width: 360px;
  max-height: 520px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  z-index: 999;
  overflow: hidden;
  border: 1px solid rgba(94,162,130,0.15);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(94,162,130,0.08), rgba(240,124,90,0.06));
  border-bottom: 1px solid rgba(94,162,130,0.1);
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.panel-icon { font-size: 24px; }
.panel-name {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}
.panel-sub {
  font-size: 11px;
  color: #a0aec0;
}
.panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.directive-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 10px;
  background: rgba(240,124,90,0.15);
  color: #f07c5a;
}
.panel-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #a0aec0;
  font-size: 16px;
  padding: 4px;
  line-height: 1;
}
.panel-close:hover { color: #718096; }

/* 偏好标签 */
.pref-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(94,162,130,0.04);
  border-bottom: 1px solid rgba(94,162,130,0.08);
  align-items: center;
}
.pref-label {
  font-size: 10px;
  color: #a0aec0;
  flex-shrink: 0;
}
.pref-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(94,162,130,0.1);
  color: #5ea282;
  font-weight: 500;
}

/* 消息区 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chat-empty {
  color: #a0aec0;
  font-size: 13px;
  line-height: 1.7;
  text-align: center;
  padding: 16px 0;
}
.chat-empty p { margin-bottom: 8px; }

.message { display: flex; flex-direction: column; }
.message.user { align-items: flex-end; }
.message.assistant { align-items: flex-start; }

.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.message.user .message-bubble {
  background: linear-gradient(135deg, #5ea282, #4a9070);
  color: white;
  border-bottom-right-radius: 4px;
}
.message.assistant .message-bubble {
  background: #f7f8fa;
  color: #2d3748;
  border-bottom-left-radius: 4px;
  border: 1px solid #edf2f7;
}

/* 思考动画 */
.thinking {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 12px 16px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a0aec0;
  animation: bounce 1.2s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}

.directive-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #f07c5a;
  display: flex;
  align-items: center;
  gap: 4px;
  padding-left: 4px;
}
.directive-icon { font-size: 12px; }

/* 输入区 */
.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #edf2f7;
  background: #fff;
}
.chat-input {
  flex: 1;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 13px;
  resize: none;
  font-family: inherit;
  color: #2d3748;
  outline: none;
  transition: border-color 0.2s;
  line-height: 1.5;
}
.chat-input:focus { border-color: #5ea282; }
.send-btn {
  padding: 0 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #5ea282, #4a9070);
  color: white;
  border: none;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.15s;
  white-space: nowrap;
}
.send-btn:hover:not(:disabled) { opacity: 0.9; transform: scale(1.02); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 面板动画 */
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.25s ease;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.97);
}

@media (max-width: 480px) {
  .assistant-panel {
    right: 0;
    bottom: 0;
    width: 100vw;
    max-height: 70vh;
    border-radius: 20px 20px 0 0;
  }
  .assistant-fab {
    bottom: 20px;
    right: 20px;
  }
}
</style>
