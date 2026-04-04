<template>
  <div class="home-page">
    <div class="blob blob--1" />
    <div class="blob blob--2" />

    <!-- 顶部导航 -->
    <nav class="navbar">
      <div class="nav-logo">
        <span>🌿</span>
        <span class="logo-name">FitGenie</span>
      </div>
      <div class="nav-actions">
        <router-link to="/history" class="nav-link">历史记录</router-link>
        <el-button size="small" @click="handleLogout">退出</el-button>
      </div>
    </nav>

    <div class="content">
      <!-- 欢迎区 -->
      <div class="hero">
        <div class="hero-left">
          <p class="greeting">{{ greeting }}，</p>
          <h1 class="hero-name">{{ profile?.name || '加载中...' }}</h1>
          <p class="hero-sub">
            今天是你健身旅程的
            <span class="highlight">第 {{ dayCount }} 天</span>
          </p>
        </div>
        <div class="hero-right">
          <div class="streak-card card">
            <div class="streak-num" ref="streakNumRef">{{ streak }}</div>
            <div class="streak-label">连续打卡</div>
            <div class="streak-unit">天</div>
            <div class="streak-flame">🔥</div>
          </div>
        </div>
      </div>

      <!-- 数据概览 -->
      <div class="stats-row">
        <div
          v-for="(stat, i) in statCards"
          :key="stat.label"
          class="stat-card card"
          :style="{ animationDelay: `${i * 0.1}s` }"
        >
          <div class="stat-icon">{{ stat.icon }}</div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-bar">
            <div class="stat-bar-fill" :style="{ width: stat.progress + '%', background: stat.color }" />
          </div>
        </div>
      </div>

      <!-- 快速操作 -->
      <div class="actions-section">
        <h2 class="section-title">今天准备好了吗？</h2>
        <div class="action-cards">
          <div class="action-card action-card--primary card" @click="router.push('/checkin')">
            <div class="action-bg" />
            <div class="action-icon">⚡</div>
            <div class="action-content">
              <div class="action-title">开始今日打卡</div>
              <div class="action-desc">输入今日数据，获取 AI 专属方案</div>
            </div>
            <div class="action-arrow">→</div>
          </div>

          <div class="action-card card" @click="router.push('/history')">
            <div class="action-icon">📊</div>
            <div class="action-content">
              <div class="action-title">查看历史记录</div>
              <div class="action-desc">体重趋势与训练回顾</div>
            </div>
            <div class="action-arrow">→</div>
          </div>
        </div>
      </div>

      <!-- 最新方案预览 -->
      <div v-if="lastCheckin" class="last-plan">
        <h2 class="section-title">上次的方案</h2>
        <div class="plan-cards">
          <div class="plan-card card">
            <div class="plan-tag">💪 训练</div>
            <p class="plan-text">{{ lastCheckin.workout_plan }}</p>
          </div>
          <div class="plan-card card">
            <div class="plan-tag">🥗 饮食</div>
            <p class="plan-text">{{ lastCheckin.diet_plan }}</p>
          </div>
        </div>
        <div class="motivation card">
          <span class="motivation-icon">✨</span>
          <p class="motivation-text">{{ lastCheckin.motivation_message }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { profileApi, dailyApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { UserProfile, DailyLogItem } from '@/api/types'

const router = useRouter()
const authStore = useAuthStore()

const profile = ref<UserProfile | null>(null)
const history = ref<DailyLogItem[]>([])
const lastCheckin = ref<any>(null)
const streak = ref(0)
const dayCount = ref(1)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 14) return '午安'
  if (h < 18) return '下午好'
  return '晚上好'
})

const statCards = computed(() => {
  const latest = history.value[0]
  return [
    {
      icon: '⚖️',
      label: '当前体重',
      value: latest?.weight_kg ? `${latest.weight_kg} kg` : '--',
      progress: latest?.weight_kg ? Math.min(100, (latest.weight_kg / 100) * 100) : 0,
      color: '#5ea282',
    },
    {
      icon: '👟',
      label: '昨日步数',
      value: latest?.steps ? `${latest.steps.toLocaleString()}` : '--',
      progress: latest?.steps ? Math.min(100, (latest.steps / 10000) * 100) : 0,
      color: '#f07c5a',
    },
    {
      icon: '🔥',
      label: '热量摄入',
      value: latest?.calories_intake ? `${latest.calories_intake} kcal` : '--',
      progress: latest?.calories_intake ? Math.min(100, (latest.calories_intake / 2500) * 100) : 0,
      color: '#f59e0b',
    },
    {
      icon: '🏋️',
      label: '训练完成',
      value: latest?.workout_done ? '已完成' : (latest ? '未完成' : '--'),
      progress: latest?.workout_done ? 100 : 0,
      color: '#8b5cf6',
    },
  ]
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  try {
    const [profileRes, historyRes] = await Promise.all([
      profileApi.get(),
      dailyApi.history(30),
    ])
    profile.value = profileRes.data
    history.value = historyRes.data

    // 计算连续打卡
    let s = 0
    for (const log of historyRes.data) {
      if (log.workout_done) s++
      else break
    }
    streak.value = s
    dayCount.value = historyRes.data.length + 1

    // 从 localStorage 读取上次打卡结果
    const saved = localStorage.getItem('lastCheckin')
    if (saved) lastCheckin.value = JSON.parse(saved)

  } catch (e) {
    ElMessage({ message: '加载数据失败', type: 'error' })
  }
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.blob {
  position: fixed;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  opacity: 0.45;
}
.blob--1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, #fcd5b8, transparent);
  top: -200px; right: -150px;
  animation: drift 16s ease-in-out infinite;
}
.blob--2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #c8e6d4, transparent);
  bottom: -150px; left: -120px;
  animation: drift 12s ease-in-out infinite reverse;
}

/* 导航 */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 40px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(254,249,243,0.8);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
}
.nav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
}
.logo-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--accent);
}
.nav-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}
.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: var(--transition);
}
.nav-link:hover { color: var(--accent); }

.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* 欢迎区 */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40px;
  animation: slideUp 0.6s ease;
}
.greeting {
  color: var(--text-secondary);
  font-size: 16px;
  margin-bottom: 4px;
}
.hero-name {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.hero-sub {
  color: var(--text-secondary);
  font-size: 15px;
}
.highlight {
  color: var(--accent);
  font-weight: 600;
}

/* 连续打卡卡片 */
.streak-card {
  width: 140px;
  height: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  cursor: default;
}
.streak-num {
  font-family: var(--font-display);
  font-size: 52px;
  font-weight: 700;
  color: var(--coral);
  line-height: 1;
}
.streak-label {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}
.streak-unit {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}
.streak-flame {
  position: absolute;
  top: 10px; right: 12px;
  font-size: 20px;
  animation: flicker 2s ease-in-out infinite;
}

/* 数据概览 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}
.stat-card {
  padding: 20px;
  animation: slideUp 0.6s ease both;
}
.stat-icon { font-size: 24px; margin-bottom: 10px; }
.stat-value {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}
.stat-bar {
  height: 3px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}
.stat-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 1s cubic-bezier(0.4,0,0.2,1);
}

/* 快速操作 */
.section-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}
.action-cards {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 40px;
}
.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.action-card--primary {
  background: linear-gradient(135deg, #5ea282, #4a9070) !important;
  border-color: transparent !important;
}
.action-card--primary .action-title,
.action-card--primary .action-desc,
.action-card--primary .action-arrow { color: white !important; }
.action-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1), transparent);
  pointer-events: none;
}
.action-icon { font-size: 32px; flex-shrink: 0; }
.action-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.action-desc {
  font-size: 13px;
  color: var(--text-secondary);
}
.action-arrow {
  margin-left: auto;
  font-size: 20px;
  color: var(--text-muted);
  transition: var(--transition);
}
.action-card:hover .action-arrow { transform: translateX(4px); }

/* 上次方案 */
.plan-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.plan-card { padding: 20px; }
.plan-tag {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.06em;
  margin-bottom: 10px;
}
.plan-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  white-space: pre-line;
  max-height: 160px;
  overflow-y: auto;
}
.motivation {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 20px;
  background: var(--coral-light) !important;
  border-color: rgba(240,124,90,0.15) !important;
}
.motivation-icon { font-size: 20px; flex-shrink: 0; }
.motivation-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  font-style: italic;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes drift {
  0%, 100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(20px,-25px) scale(1.04); }
  66% { transform: translate(-15px,15px) scale(0.96); }
}
@keyframes flicker {
  0%, 100% { transform: scale(1) rotate(-5deg); }
  50% { transform: scale(1.1) rotate(5deg); }
}

@media (max-width: 768px) {
  .navbar { padding: 16px 20px; }
  .content { padding: 24px 16px 60px; }
  .hero { flex-direction: column; align-items: flex-start; gap: 20px; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .action-cards { grid-template-columns: 1fr; }
  .plan-cards { grid-template-columns: 1fr; }
}
</style>