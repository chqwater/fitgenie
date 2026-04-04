<template>
  <div class="auth-page">
    <div class="blob blob--1" />
    <div class="blob blob--2" />

    <div class="register-wrap">
      <!-- Logo -->
      <div class="logo" @click="router.push('/login')">
        <span>🌿</span>
        <span class="logo-name">FitGenie</span>
      </div>

      <div class="register-card card">
        <!-- 步骤指示器 -->
        <div class="steps">
          <div
            v-for="(s, i) in stepLabels"
            :key="i"
            class="step"
            :class="{ active: step === i + 1, done: step > i + 1 }"
          >
            <div class="step-dot">
              <span v-if="step > i + 1">✓</span>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <span class="step-label">{{ s }}</span>
          </div>
          <div class="step-line" :style="{ width: step === 1 ? '0%' : '100%' }" />
        </div>

        <!-- Step 1：账号信息 -->
        <transition name="step-slide" mode="out-in">
          <div v-if="step === 1" key="step1" class="step-content">
            <div class="step-header">
              <h2 class="step-title">创建你的账号</h2>
              <p class="step-sub">填写基本信息，开始你的健身旅程</p>
            </div>

            <el-form
              ref="form1Ref"
              :model="form"
              :rules="rules1"
              label-position="top"
            >
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="form.username"
                  placeholder="设置一个独特的用户名"
                  size="large"
                  prefix-icon="User"
                />
              </el-form-item>
              <el-form-item label="昵称" prop="name">
                <el-input
                  v-model="form.name"
                  placeholder="你希望我们怎么称呼你？"
                  size="large"
                  prefix-icon="StarFilled"
                />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="form.password"
                  type="password"
                  placeholder="至少6位"
                  size="large"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-button
                class="submit-btn"
                type="primary"
                size="large"
                @click="nextStep"
              >
                下一步 →
              </el-button>
            </el-form>
          </div>

          <!-- Step 2：身体数据 -->
          <div v-else key="step2" class="step-content">
            <div class="step-header">
              <h2 class="step-title">告诉我们关于你</h2>
              <p class="step-sub">AI 将根据这些数据为你定制专属方案</p>
            </div>

            <el-form
              ref="form2Ref"
              :model="form"
              :rules="rules2"
              label-position="top"
            >
              <div class="form-row">
                <el-form-item label="年龄" prop="age">
                  <el-input
                    v-model.number="form.age"
                    placeholder="岁"
                    size="large"
                    type="number"
                  />
                </el-form-item>
                <el-form-item label="身高 (cm)" prop="height_cm">
                  <el-input
                    v-model.number="form.height_cm"
                    placeholder="cm"
                    size="large"
                    type="number"
                  />
                </el-form-item>
              </div>

              <el-form-item label="当前体重 (kg)" prop="weight_kg">
                <el-input
                  v-model.number="form.weight_kg"
                  placeholder="kg"
                  size="large"
                  type="number"
                />
              </el-form-item>

              <el-form-item label="训练目标" prop="goal">
                <div class="goal-options">
                  <div
                    v-for="g in goalOptions"
                    :key="g.value"
                    class="goal-card"
                    :class="{ selected: form.goal === g.value }"
                    @click="form.goal = g.value"
                  >
                    <span class="goal-icon">{{ g.icon }}</span>
                    <span class="goal-label">{{ g.label }}</span>
                  </div>
                </div>
              </el-form-item>

              <el-form-item label="活动水平" prop="activity_level">
                <el-select
                  v-model="form.activity_level"
                  placeholder="选择你的日常活动水平"
                  size="large"
                  style="width: 100%"
                >
                  <el-option label="久坐（几乎不运动）" value="sedentary" />
                  <el-option label="轻度（每周1-3次运动）" value="light" />
                  <el-option label="中度（每周3-5次运动）" value="moderate" />
                  <el-option label="高强度（每天运动）" value="active" />
                </el-select>
              </el-form-item>

              <el-form-item label="饮食偏好" prop="dietary_pref">
                <el-select
                  v-model="form.dietary_pref"
                  placeholder="选择饮食偏好"
                  size="large"
                  style="width: 100%"
                >
                  <el-option label="无限制" value="no restriction" />
                  <el-option label="素食" value="vegetarian" />
                  <el-option label="纯素" value="vegan" />
                  <el-option label="低碳水" value="low_carb" />
                </el-select>
              </el-form-item>

              <div class="btn-row">
                <el-button size="large" @click="step = 1">← 上一步</el-button>
                <el-button
                  class="submit-btn-sm"
                  type="primary"
                  size="large"
                  :loading="loading"
                  @click="handleRegister"
                >
                  {{ loading ? '创建中...' : '开始训练 🚀' }}
                </el-button>
              </div>
            </el-form>
          </div>
        </transition>
      </div>

      <p class="footnote">
        已有账号？
        <router-link to="/login" class="link">立即登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const step = ref(1)
const loading = ref(false)
const form1Ref = ref()
const form2Ref = ref()

const stepLabels = ['账号信息', '身体数据']

const goalOptions = [
  { value: 'lose_fat', icon: '🔥', label: '减脂' },
  { value: 'build_muscle', icon: '💪', label: '增肌' },
  { value: 'maintain', icon: '⚖️', label: '维持' },
]

const form = reactive({
  username: '',
  password: '',
  name: '',
  age: null as number | null,
  weight_kg: null as number | null,
  height_cm: null as number | null,
  goal: 'lose_fat',
  activity_level: '',
  dietary_pref: '',
})

const rules1 = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '至少6位', trigger: 'blur' },
  ],
}

const rules2 = {
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
  weight_kg: [{ required: true, message: '请输入体重', trigger: 'blur' }],
  height_cm: [{ required: true, message: '请输入身高', trigger: 'blur' }],
  activity_level: [{ required: true, message: '请选择活动水平', trigger: 'change' }],
  dietary_pref: [{ required: true, message: '请选择饮食偏好', trigger: 'change' }],
}

async function nextStep() {
  await form1Ref.value?.validate()
  step.value = 2
}

async function handleRegister() {
  await form2Ref.value?.validate()
  loading.value = true
  try {
    await authStore.register(form as any)
    ElMessage({ message: '注册成功，欢迎加入 FitGenie 🎉', type: 'success' })
    router.push('/')
  } catch (e: any) {
    ElMessage({ message: e.response?.data?.detail || '注册失败', type: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  position: relative;
  overflow: hidden;
}

.blob {
  position: fixed;
  border-radius: 50%;
  filter: blur(70px);
  pointer-events: none;
  opacity: 0.5;
}
.blob--1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #fcd5b8, transparent);
  top: -150px; right: -100px;
  animation: drift 14s ease-in-out infinite;
}
.blob--2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #c8e6d4, transparent);
  bottom: -100px; left: -80px;
  animation: drift 11s ease-in-out infinite reverse;
}

.register-wrap {
  width: 100%;
  max-width: 520px;
  position: relative;
  z-index: 10;
  animation: slideUp 0.6s cubic-bezier(0.4,0,0.2,1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  cursor: pointer;
  font-size: 20px;
}
.logo-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--accent);
}

.register-card {
  padding: 40px;
}

/* 步骤条 */
.steps {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 36px;
  position: relative;
}
.step {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.step-dot {
  width: 28px; height: 28px;
  border-radius: 50%;
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  background: white;
  transition: var(--transition);
  flex-shrink: 0;
}
.step.active .step-dot {
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-light);
}
.step.done .step-dot {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
.step-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  transition: var(--transition);
}
.step.active .step-label { color: var(--accent); }
.step.done .step-label { color: var(--text-secondary); }
.step-line {
  position: absolute;
  top: 14px; left: 40px;
  height: 2px;
  background: var(--accent);
  transition: width 0.5s cubic-bezier(0.4,0,0.2,1);
  z-index: -1;
}

.step-header { margin-bottom: 28px; }
.step-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.step-sub {
  color: var(--text-secondary);
  font-size: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* 目标选择 */
.goal-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
}
.goal-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 8px;
  border-radius: var(--radius-sm);
  border: 1.5px solid var(--border);
  background: rgba(255,255,255,0.6);
  cursor: pointer;
  transition: var(--transition);
}
.goal-card:hover {
  border-color: var(--accent);
  background: var(--accent-light);
  transform: translateY(-2px);
}
.goal-card.selected {
  border-color: var(--accent);
  background: var(--accent-light);
  box-shadow: 0 0 0 3px var(--accent-light);
}
.goal-icon { font-size: 24px; }
.goal-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
.goal-card.selected .goal-label { color: var(--accent); }

.submit-btn {
  width: 100%;
  height: 52px !important;
  border-radius: var(--radius-sm) !important;
  font-size: 15px !important;
  margin-top: 8px;
}
.btn-row {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
.btn-row .el-button { height: 52px !important; border-radius: var(--radius-sm) !important; }
.submit-btn-sm {
  flex: 1;
  font-size: 15px !important;
}

.footnote {
  text-align: center;
  margin-top: 20px;
  color: var(--text-muted);
  font-size: 14px;
}
.link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
}
.link:hover { color: #4a9070; }

/* 步骤切换动画 */
.step-slide-enter-active, .step-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
}
.step-slide-enter-from {
  opacity: 0; transform: translateX(24px);
}
.step-slide-leave-to {
  opacity: 0; transform: translateX(-24px);
}

@keyframes drift {
  0%, 100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(20px,-25px) scale(1.04); }
  66% { transform: translate(-15px,15px) scale(0.96); }
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>