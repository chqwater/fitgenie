<template>
  <div class="checkin-page">
    <div class="blob blob--1" />
    <div class="blob blob--2" />


    <!-- 导航 -->
    <nav class="navbar">
      <div class="nav-left" @click="router.push('/')">
        <span class="back-arrow">←</span>
        <span class="logo-name">FitGenie</span>
      </div>
      <div class="nav-title">今日打卡</div>
    </nav>

    <div class="content">
      <!-- 输入阶段 -->
      <transition name="fade" mode="out-in">
        <div v-if="!result" key="form" class="form-section">
          <div class="form-header">
            <h1 class="page-title">记录今天</h1>
            <p class="page-sub">AI 将根据你的数据生成专属方案</p>
          </div>

          <div class="input-grid">
            <!-- 体重 -->
            <div class="input-card card">
              <div class="input-label">
                <span class="input-icon">⚖️</span>
                今日体重
              </div>
              <div class="weight-input">
                <button class="adj-btn" @click="adjust('weight_kg', -0.1)">−</button>
                <div class="weight-display">
                  <span class="weight-num">{{ form.weight_kg.toFixed(1) }}</span>
                  <span class="weight-unit">kg</span>
                </div>
                <button class="adj-btn" @click="adjust('weight_kg', 0.1)">+</button>
              </div>
            </div>

            <!-- 步数 -->
            <div class="input-card card">
              <div class="input-label">
                <span class="input-icon">👟</span>
                今日步数
              </div>
              <div class="steps-display">
                <el-slider
                  v-model="form.steps"
                  :min="0"
                  :max="20000"
                  :step="100"
                  :show-tooltip="true"
                  :format-tooltip="(v: number) => `${v.toLocaleString()} 步`"
                />
                <div class="steps-num">{{ form.steps.toLocaleString() }} 步</div>
              </div>
            </div>

            <!-- 热量 -->
            <div class="input-card card">
              <div class="input-label">
                <span class="input-icon">🍽️</span>
                今日饮食热量
              </div>
              <div class="weight-input">
                <button class="adj-btn" @click="adjust('calories_intake', -50)">−</button>
                <div class="weight-display">
                  <span class="weight-num">{{ form.calories_intake }}</span>
                  <span class="weight-unit">kcal</span>
                </div>
                <button class="adj-btn" @click="adjust('calories_intake', 50)">+</button>
              </div>
            </div>

            <!-- 训练完成 -->
            <div class="input-card card">
              <div class="input-label">
                <span class="input-icon">🏋️</span>
                完成训练了吗？
              </div>
              <div class="workout-toggle">
                <div
                  class="toggle-option"
                  :class="{ active: form.workout_done }"
                  @click="form.workout_done = true"
                >
                  <span>✓</span> 完成了
                </div>
                <div
                  class="toggle-option toggle-option--no"
                  :class="{ active: !form.workout_done }"
                  @click="form.workout_done = false"
                >
                  <span>✗</span> 没有
                </div>
              </div>
            </div>
          </div>

          <!-- 情绪选择 -->
          <div class="mood-section card">
            <div class="input-label">
              <span class="input-icon">💭</span>
              今天感觉怎么样？
            </div>
            <div class="mood-options">
              <div
                v-for="m in moods"
                :key="m.value"
                class="mood-card"
                :class="{ selected: form.mood === m.value }"
                @click="form.mood = m.value"
              >
                <div class="mood-emoji">{{ m.emoji }}</div>
                <div class="mood-label">{{ m.label }}</div>
              </div>
            </div>
          </div>

          <!-- 提交 -->
          <el-button
            class="submit-btn"
            type="primary"
            size="large"
            :loading="loading"
            @click="handleCheckin"
          >
            <span v-if="!loading">获取今日方案 ✨</span>
            <span v-else>AI 正在生成你的专属方案...</span>
          </el-button>

          <p v-if="loading" class="loading-tip">
            {{ loadingTips[tipIndex] }}
          </p>
        </div>

        <!-- 结果阶段 -->
        <div v-else key="result" class="result-section">
          <div class="result-header">
            <div class="result-badge" :class="`mode--${result.mode}`">
              {{ modeLabel[result.mode] }}
            </div>
            <h1 class="result-title">今日方案已生成</h1>
            <p class="result-date">{{ result.date }}</p>
          </div>

          <!-- 趋势分析 -->
          <div class="result-card card trend-card">
            <div class="card-tag">📈 趋势分析</div>
            <p class="card-text">{{ result.trend_summary }}</p>
          </div>

          <!-- 训练 + 饮食 -->
          <div class="result-grid">
            <div class="result-card card">
              <div class="card-tag workout-tag">💪 训练计划</div>
              <pre class="card-text">{{ result.workout_plan }}</pre>
            </div>
            <div class="result-card card">
              <div class="card-tag diet-tag">🥗 饮食方案</div>
              <pre class="card-text">{{ result.diet_plan }}</pre>
            </div>
          </div>

          <!-- 教练寄语 -->
          <div class="motivation-card card">
            <div class="motivation-inner">
              <span class="motivation-icon">✨</span>
              <div>
                <div class="motivation-from">来自你的 AI 教练</div>
                <p class="motivation-text">{{ result.motivation_message }}</p>
              </div>
            </div>
          </div>

          <!-- 重新生成 -->
          <div class="regenerate-section card">
            <div class="regenerate-inner">
              <div class="regenerate-left">
                <div class="regenerate-title">对方案不满意？</div>
                <div class="regenerate-sub">
                  <span v-if="pendingDirectives">
                    ⚡ 小助手已记录你的调整意见，点击重新生成
                  </span>
                  <span v-else>
                    点击右下角 🤖 小助手告诉我你的想法，或直接重新生成
                  </span>
                </div>
              </div>
              <el-button
                class="regen-btn"
                :loading="regenerating"
                @click="handleRegenerate"
              >
                <span v-if="!regenerating">{{ pendingDirectives ? '✨ 个性化重新生成' : '🔄 重新生成' }}</span>
                <span v-else>AI 重新规划中...</span>
              </el-button>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="result-actions">
            <el-button size="large" @click="router.push('/')">回到主页</el-button>
            <el-button size="large" @click="router.push('/history')">查看历史</el-button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { dailyApi, profileApi } from '@/api'
import type { CheckinResponse } from '@/api/types'
import { useAssistantStore } from '@/stores/assistant'

const router = useRouter()
const assistantStore = useAssistantStore()
const loading = ref(false)
const regenerating = ref(false)
const result = ref<CheckinResponse | null>(null)
const tipIndex = ref(0)
const pendingDirectives = computed(() => assistantStore.pendingDirectives)
let tipTimer: ReturnType<typeof setInterval>

const loadingTips = [
  '正在分析你的体重趋势...',
  'Analyst Agent 检测是否停滞...',
  'Orchestrator 正在仲裁决策...',
  'Coach Agent 生成训练计划...',
  'Diet Agent 计算热量方案...',
  'Mental Agent 准备激励消息...',
]

const moods: { value: 'good' | 'neutral' | 'tired'; emoji: string; label: string }[] = [
  { value: 'good', emoji: '😄', label: '状态很好' },
  { value: 'neutral', emoji: '😐', label: '一般般' },
  { value: 'tired', emoji: '😴', label: '有点累' },
]

const modeLabel: Record<string, string> = {
  normal: '✅ 正常模式',
  aggressive: '🔥 进取模式',
  conservative: '🛡️ 保守模式',
}

const form = reactive({
  weight_kg: 75.0,
  steps: 8000,
  calories_intake: 2000,
  workout_done: true,
  mood: 'neutral' as 'good' | 'neutral' | 'tired',
})

function adjust(field: 'weight_kg' | 'calories_intake', delta: number) {
  if (field === 'weight_kg') {
    form.weight_kg = Math.max(30, Math.round((form.weight_kg + delta) * 10) / 10)
  } else {
    form.calories_intake = Math.max(0, form.calories_intake + delta)
  }
}

async function handleCheckin() {
  loading.value = true
  tipIndex.value = 0
  tipTimer = setInterval(() => {
    tipIndex.value = (tipIndex.value + 1) % loadingTips.length
  }, 3000)

  try {
    const res = await dailyApi.checkin(form)
    result.value = res.data
    assistantStore.setCurrentPlan(res.data)
    localStorage.setItem('lastCheckin', JSON.stringify(res.data))
    ElMessage({ message: '方案生成成功 🎉', type: 'success' })
  } catch (e: any) {
    ElMessage({ message: e.response?.data?.detail || '打卡失败，请重试', type: 'error' })
  } finally {
    loading.value = false
    clearInterval(tipTimer)
  }
}

async function handleRegenerate() {
  regenerating.value = true
  tipIndex.value = 0
  tipTimer = setInterval(() => {
    tipIndex.value = (tipIndex.value + 1) % loadingTips.length
  }, 3000)

  try {
    const directives = assistantStore.pendingDirectives ?? null
    const res = await dailyApi.regenerate({ ...form, directives })
    result.value = res.data
    assistantStore.setCurrentPlan(res.data)
    assistantStore.clearDirectives()
    localStorage.setItem('lastCheckin', JSON.stringify(res.data))
    ElMessage({ message: directives ? '个性化方案已重新生成 ✨' : '方案已重新生成 🔄', type: 'success' })
  } catch (e: any) {
    ElMessage({ message: e.response?.data?.detail || '重新生成失败，请重试', type: 'error' })
  } finally {
    regenerating.value = false
    clearInterval(tipTimer)
  }
}

onMounted(async () => {
  try {
    const res = await profileApi.get()
    form.weight_kg = res.data.weight_kg
  } catch {}
})

onUnmounted(() => clearInterval(tipTimer))
</script>

<style scoped>
.checkin-page {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.blob {
  position: fixed;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  opacity: 0.4;
}
.blob--1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #fcd5b8, transparent);
  top: -100px; right: -100px;
  animation: drift 14s ease-in-out infinite;
}
.blob--2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #c8e6d4, transparent);
  bottom: -100px; left: -80px;
  animation: drift 11s ease-in-out infinite reverse;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 40px;
  position: sticky; top: 0; z-index: 100;
  background: rgba(254,249,243,0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
}
.nav-left {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  transition: var(--transition);
}
.nav-left:hover { color: var(--accent); }
.back-arrow { font-size: 18px; }
.logo-name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--accent);
}
.nav-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.content {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

.form-header { margin-bottom: 32px; }
.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.page-sub { color: var(--text-secondary); font-size: 15px; }

/* 输入网格 */
.input-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.input-card { padding: 24px; }
.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.04em;
  margin-bottom: 16px;
}
.input-icon { font-size: 18px; }

/* 体重调节 */
.weight-input {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.adj-btn {
  width: 36px; height: 36px;
  border-radius: 50%;
  border: 1.5px solid var(--border);
  background: white;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: var(--transition);
  flex-shrink: 0;
}
.adj-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-light);
}
.weight-display { text-align: center; }
.weight-num {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
}
.weight-unit {
  font-size: 14px;
  color: var(--text-muted);
  margin-left: 4px;
}

/* 步数滑块 */
.steps-display { width: 100%; }
.steps-num {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 8px;
}

/* 训练开关 */
.workout-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.toggle-option {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border);
  background: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: var(--transition);
}
.toggle-option.active {
  border-color: var(--accent);
  background: var(--accent-light);
  color: var(--accent);
}
.toggle-option--no.active {
  border-color: var(--coral);
  background: var(--coral-light);
  color: var(--coral);
}

/* 情绪 */
.mood-section {
  padding: 24px;
  margin-bottom: 24px;
}
.mood-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.mood-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 12px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border);
  background: rgba(255,255,255,0.6);
  cursor: pointer;
  transition: var(--transition);
}
.mood-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.mood-card.selected {
  border-color: var(--accent);
  background: var(--accent-light);
  box-shadow: 0 0 0 3px var(--accent-light);
}
.mood-emoji { font-size: 32px; }
.mood-label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.mood-card.selected .mood-label { color: var(--accent); }

.submit-btn {
  width: 100%;
  height: 56px !important;
  font-size: 16px !important;
  border-radius: var(--radius-sm) !important;
}
.loading-tip {
  text-align: center;
  margin-top: 16px;
  color: var(--text-muted);
  font-size: 13px;
  font-style: italic;
  animation: pulse 2s ease-in-out infinite;
}

/* 结果 */
.result-header {
  text-align: center;
  margin-bottom: 32px;
  animation: slideUp 0.5s ease;
}
.result-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
  letter-spacing: 0.04em;
}
.mode--normal { background: rgba(94,162,130,0.15); color: var(--accent); }
.mode--aggressive { background: rgba(240,124,90,0.15); color: var(--coral); }
.mode--conservative { background: rgba(245,158,11,0.15); color: #d97706; }
.result-title {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.result-date { color: var(--text-muted); font-size: 14px; }

.trend-card {
  padding: 24px;
  margin-bottom: 16px;
  animation: slideUp 0.5s ease 0.1s both;
}
.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
  animation: slideUp 0.5s ease 0.2s both;
}
.result-card { padding: 24px; }
.card-tag {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--accent);
  margin-bottom: 12px;
}
.workout-tag { color: var(--coral); }
.diet-tag { color: var(--accent); }
.card-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
  font-family: var(--font-body);
  max-height: 240px;
  overflow-y: auto;
}

.motivation-card {
  padding: 24px;
  background: linear-gradient(135deg, rgba(94,162,130,0.08), rgba(240,124,90,0.08)) !important;
  margin-bottom: 32px;
  animation: slideUp 0.5s ease 0.3s both;
}
.motivation-inner {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.motivation-icon { font-size: 24px; flex-shrink: 0; }
.motivation-from {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}
.motivation-text {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.7;
  font-style: italic;
}

.regenerate-section {
  padding: 20px 24px;
  margin-bottom: 16px;
  animation: slideUp 0.5s ease 0.35s both;
  background: linear-gradient(135deg, rgba(94,162,130,0.05), rgba(240,124,90,0.05)) !important;
  border: 1.5px solid rgba(94,162,130,0.15) !important;
}
.regenerate-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.regenerate-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.regenerate-sub {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}
.regen-btn {
  flex-shrink: 0;
  height: 40px !important;
  padding: 0 20px !important;
  border-radius: var(--radius-sm) !important;
  font-size: 13px !important;
  background: linear-gradient(135deg, #5ea282, #f07c5a) !important;
  border: none !important;
  color: white !important;
}
.regen-btn:hover:not(:disabled) {
  opacity: 0.9 !important;
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  animation: slideUp 0.5s ease 0.4s both;
}
.result-actions .el-button {
  height: 48px !important;
  padding: 0 32px !important;
  border-radius: var(--radius-sm) !important;
  font-size: 14px !important;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes drift {
  0%, 100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(20px,-25px) scale(1.04); }
  66% { transform: translate(-15px,15px) scale(0.96); }
}
@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

@media (max-width: 768px) {
  .navbar { padding: 16px 20px; }
  .input-grid { grid-template-columns: 1fr; }
  .result-grid { grid-template-columns: 1fr; }
}
</style>