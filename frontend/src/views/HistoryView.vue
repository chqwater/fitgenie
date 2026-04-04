<template>
  <div class="history-page">
    <div class="blob blob--1" />
    <div class="blob blob--2" />

    <nav class="navbar">
      <div class="nav-left" @click="router.push('/')">
        <span class="back-arrow">←</span>
        <span class="logo-name">FitGenie</span>
      </div>
      <div class="nav-title">历史记录</div>
    </nav>

    <div class="content">
      <div class="page-header">
        <h1 class="page-title">你的旅程</h1>
        <p class="page-sub">每一天的坚持都在这里</p>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-dots">
          <span /><span /><span />
        </div>
        <p>加载数据中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!logs.length" class="empty-state card">
        <div class="empty-icon">🌱</div>
        <h3 class="empty-title">还没有记录</h3>
        <p class="empty-desc">完成第一次打卡，开始你的健身旅程</p>
        <el-button type="primary" size="large" @click="router.push('/checkin')">
          立即打卡
        </el-button>
      </div>

      <template v-else>
        <!-- 统计概览 -->
        <div class="overview-grid">
          <div
            v-for="(stat, i) in overviewStats"
            :key="stat.label"
            class="overview-card card"
            :style="{ animationDelay: `${i * 0.08}s` }"
          >
            <div class="overview-icon">{{ stat.icon }}</div>
            <div class="overview-value">{{ stat.value }}</div>
            <div class="overview-label">{{ stat.label }}</div>
          </div>
        </div>

        <!-- 体重趋势图 -->
        <div class="chart-section card">
          <div class="chart-header">
            <div class="chart-title">体重趋势</div>
            <div class="chart-legend">
              <span class="legend-dot" />
              <span class="legend-label">体重 (kg)</span>
            </div>
          </div>
          <div class="chart-wrap">
            <svg
              class="weight-chart"
              viewBox="0 0 600 160"
              preserveAspectRatio="none"
            >
              <!-- 网格线 -->
              <line
                v-for="i in 4"
                :key="i"
                x1="0" :y1="i * 32"
                x2="600" :y2="i * 32"
                stroke="rgba(0,0,0,0.04)"
                stroke-width="1"
              />
              <!-- 面积填充 -->
              <path
                v-if="chartPath"
                :d="chartArea"
                fill="url(#areaGrad)"
              />
              <!-- 折线 -->
              <path
                v-if="chartPath"
                :d="chartPath"
                fill="none"
                stroke="url(#lineGrad)"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="chart-line"
              />
              <!-- 数据点 -->
              <circle
                v-for="(pt, i) in chartPoints"
                :key="i"
                :cx="pt.x" :cy="pt.y"
                r="4"
                fill="white"
                stroke="#5ea282"
                stroke-width="2"
                class="chart-dot"
              >
                <title>{{ chartLabels[i] }}: {{ pt.weight }}kg</title>
              </circle>
              <!-- 渐变定义 -->
              <defs>
                <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stop-color="#5ea282" />
                  <stop offset="100%" stop-color="#f07c5a" />
                </linearGradient>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#5ea282" stop-opacity="0.15" />
                  <stop offset="100%" stop-color="#5ea282" stop-opacity="0" />
                </linearGradient>
              </defs>
            </svg>
            <!-- X轴标签 -->
            <div class="chart-xlabels">
              <span
                v-for="(label, i) in chartLabels"
                :key="i"
                class="chart-xlabel"
              >{{ label }}</span>
            </div>
          </div>
        </div>

        <!-- 日志列表 -->
        <div class="logs-section">
          <div class="logs-title">打卡记录</div>
          <div class="logs-list">
            <div
              v-for="(log, i) in logs"
              :key="log.date"
              class="log-item card"
              :style="{ animationDelay: `${i * 0.05}s` }"
            >
              <div class="log-date">
                <div class="log-day">{{ formatDay(log.date) }}</div>
                <div class="log-month">{{ formatMonth(log.date) }}</div>
              </div>
              <div class="log-divider" />
              <div class="log-stats">
                <div class="log-stat">
                  <span class="log-stat-icon">⚖️</span>
                  <span class="log-stat-val">{{ log.weight_kg ?? '--' }} kg</span>
                </div>
                <div class="log-stat">
                  <span class="log-stat-icon">👟</span>
                  <span class="log-stat-val">{{ log.steps?.toLocaleString() ?? '--' }}</span>
                </div>
                <div class="log-stat">
                  <span class="log-stat-icon">🍽️</span>
                  <span class="log-stat-val">{{ log.calories_intake ?? '--' }} kcal</span>
                </div>
              </div>
              <div class="log-badges">
                <span
                  class="log-badge"
                  :class="log.workout_done ? 'badge--done' : 'badge--skip'"
                >
                  {{ log.workout_done ? '✓ 训练' : '✗ 休息' }}
                </span>
                <span class="log-badge badge--mood">
                  {{ moodEmoji[log.mood ?? 'neutral'] }}
                  {{ moodLabel[log.mood ?? 'neutral'] }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { dailyApi } from '@/api'
import type { DailyLogItem } from '@/api/types'

const router = useRouter()
const loading = ref(true)
const logs = ref<DailyLogItem[]>([])

const moodEmoji: Record<string, string> = {
  good: '😄', neutral: '😐', tired: '😴',
}
const moodLabel: Record<string, string> = {
  good: '状态好', neutral: '一般', tired: '疲惫',
}

// 统计概览
const overviewStats = computed(() => {
  const validWeights = logs.value
    .map(l => l.weight_kg)
    .filter((w): w is number => w !== null)

  const workoutDays = logs.value.filter(l => l.workout_done).length
  const totalDays = logs.value.length

  const weightChange = validWeights.length >= 2
  ? ((validWeights[validWeights.length - 1]! - validWeights[0]!)).toFixed(1)
  : '--'

  const avgSteps = logs.value.length
    ? Math.round(logs.value.reduce((s, l) => s + (l.steps ?? 0), 0) / logs.value.length)
    : 0

  return [
    { icon: '📅', label: '记录天数', value: `${totalDays} 天` },
    { icon: '🏋️', label: '训练完成', value: `${workoutDays} 次` },
    {
      icon: '📉',
      label: '体重变化',
      value: weightChange === '--' ? '--' : `${Number(weightChange) > 0 ? '+' : ''}${weightChange} kg`,
    },
    { icon: '👟', label: '日均步数', value: avgSteps ? avgSteps.toLocaleString() : '--' },
  ]
})

// SVG 折线图数据
const chartPoints = computed(() => {
  const weightLogs = [...logs.value]
    .reverse()
    .filter(l => l.weight_kg !== null)
    .slice(-14)

  if (weightLogs.length < 2) return []

  const weights = weightLogs.map(l => l.weight_kg as number)
  const minW = Math.min(...weights) - 1
  const maxW = Math.max(...weights) + 1
  const range = maxW - minW || 1

  return weightLogs.map((log, i) => ({
    x: (i / (weightLogs.length - 1)) * 580 + 10,
    y: 140 - ((log.weight_kg! - minW) / range) * 120,
    weight: log.weight_kg,
  }))
})

const chartLabels = computed(() =>
  [...logs.value]
    .reverse()
    .filter(l => l.weight_kg !== null)
    .slice(-14)
    .map(l => formatDay(l.date))
)

const chartPath = computed(() => {
  const pts = chartPoints.value
  if (pts.length < 2) return ''
  return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
})

const chartArea = computed(() => {
  const pts = chartPoints.value
  if (pts.length < 2) return ''
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const last = pts[pts.length - 1]!
  const first = pts[0]!
  return `${line} L ${last.x} 160 L ${first.x} 160 Z`
})

function formatDay(dateStr: string) {
  return new Date(dateStr).getDate() + '日'
}
function formatMonth(dateStr: string) {
  return (new Date(dateStr).getMonth() + 1) + '月'
}

onMounted(async () => {
  try {
    const res = await dailyApi.history(30)
    logs.value = res.data
  } catch {
    ElMessage({ message: '加载失败', type: 'error' })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.history-page {
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
  top: -120px; right: -100px;
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
.nav-title { font-size: 14px; font-weight: 500; color: var(--text-secondary); }

.content {
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

.page-header { margin-bottom: 32px; }
.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.page-sub { color: var(--text-secondary); font-size: 15px; }

/* 加载 */
.loading-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
}
.loading-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}
.loading-dots span {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--accent);
  animation: bounce 1.2s ease-in-out infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 64px 40px;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.empty-desc { color: var(--text-secondary); font-size: 14px; margin-bottom: 24px; }

/* 概览 */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.overview-card {
  padding: 20px;
  text-align: center;
  animation: slideUp 0.5s ease both;
}
.overview-icon { font-size: 24px; margin-bottom: 10px; }
.overview-value {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.overview-label { font-size: 12px; color: var(--text-muted); }

/* 图表 */
.chart-section {
  padding: 24px;
  margin-bottom: 24px;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.chart-legend {
  display: flex;
  align-items: center;
  gap: 6px;
}
.legend-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--accent);
}
.legend-label { font-size: 12px; color: var(--text-muted); }
.weight-chart {
  width: 100%;
  height: 160px;
  display: block;
}
.chart-line {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: drawLine 1.5s ease forwards;
}
.chart-dot {
  opacity: 0;
  animation: fadeIn 0.3s ease forwards;
}
.chart-xlabels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  padding: 0 10px;
}
.chart-xlabel { font-size: 11px; color: var(--text-muted); }

/* 日志列表 */
.logs-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}
.logs-list { display: flex; flex-direction: column; gap: 10px; }
.log-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  animation: slideUp 0.4s ease both;
}
.log-date { text-align: center; flex-shrink: 0; width: 44px; }
.log-day {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}
.log-month { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.log-divider {
  width: 1px;
  height: 40px;
  background: var(--border);
  flex-shrink: 0;
}
.log-stats {
  display: flex;
  gap: 20px;
  flex: 1;
}
.log-stat {
  display: flex;
  align-items: center;
  gap: 6px;
}
.log-stat-icon { font-size: 14px; }
.log-stat-val { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.log-badges {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.log-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.badge--done { background: var(--accent-light); color: var(--accent); }
.badge--skip { background: rgba(240,124,90,0.1); color: var(--coral); }
.badge--mood { background: rgba(0,0,0,0.04); color: var(--text-secondary); }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes drift {
  0%, 100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(20px,-25px) scale(1.04); }
  66% { transform: translate(-15px,15px) scale(0.96); }
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
@keyframes drawLine {
  to { stroke-dashoffset: 0; }
}
@keyframes fadeIn {
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .navbar { padding: 16px 20px; }
  .overview-grid { grid-template-columns: repeat(2, 1fr); }
  .log-item { flex-wrap: wrap; }
  .log-stats { flex-wrap: wrap; gap: 12px; }
}
</style>