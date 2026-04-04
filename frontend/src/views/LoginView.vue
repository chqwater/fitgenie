<template>
  <div class="auth-page">
    <!-- 浮动背景装饰 -->
    <div class="blob blob--1" />
    <div class="blob blob--2" />
    <div class="blob blob--3" />

    <div class="auth-wrap">
      <!-- 左侧品牌区 -->
      <div class="brand-side">
        <div class="brand-inner">
          <div class="logo">
            <span class="logo-icon">🌿</span>
            <span class="logo-name">FitGenie</span>
          </div>
          <h1 class="brand-title">
            Your Personal<br>
            <em>AI Coach</em><br>
            Awaits
          </h1>
          <p class="brand-desc">
            多智能体驱动的个性化健身系统，每天为你生成专属的训练与饮食方案。
          </p>
          <div class="brand-stats">
            <div class="stat" v-for="s in stats" :key="s.label">
              <span class="stat-num">{{ s.num }}</span>
              <span class="stat-label">{{ s.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="form-side">
        <div class="form-card card">
          <div class="form-header">
            <h2 class="form-title">欢迎回来</h2>
            <p class="form-sub">登录你的 FitGenie 账号</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="form.username"
                placeholder="输入用户名"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-button
              class="submit-btn"
              type="primary"
              size="large"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '开始今天的训练 →' }}
            </el-button>
          </el-form>

          <div class="divider">
            <span>还没有账号？</span>
          </div>

          <router-link to="/register">
            <el-button class="register-btn" size="large">
              免费注册
            </el-button>
          </router-link>
        </div>

        <!-- 底部装饰文字 -->
        <p class="footnote">科学训练 · 智能饮食 · 持续进步</p>
      </div>
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
const formRef = ref()
const loading = ref(false)

const stats = [
  { num: '5+', label: 'AI Agents' },
  { num: '∞', label: '个性化方案' },
  { num: '24/7', label: '持续追踪' },
]

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value?.validate()
  loading.value = true
  try {
    await authStore.login(form)
    ElMessage({ message: '登录成功 💪', type: 'success' })
    router.push('/')
  } catch (e: any) {
    ElMessage({ message: e.response?.data?.detail || '用户名或密码错误', type: 'error' })
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
  position: relative;
  overflow: hidden;
  padding: 24px;
}

/* 浮动色块 */
.blob {
  position: fixed;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
  opacity: 0.6;
}
.blob--1 {
  width: 480px; height: 480px;
  background: radial-gradient(circle, #fcd5b8, transparent);
  top: -120px; right: -80px;
  animation: drift 12s ease-in-out infinite;
}
.blob--2 {
  width: 360px; height: 360px;
  background: radial-gradient(circle, #c8e6d4, transparent);
  bottom: -80px; left: -60px;
  animation: drift 15s ease-in-out infinite reverse;
}
.blob--3 {
  width: 280px; height: 280px;
  background: radial-gradient(circle, #fde8c8, transparent);
  top: 50%; left: 30%;
  animation: drift 10s ease-in-out infinite 2s;
}

.auth-wrap {
  display: flex;
  gap: 64px;
  align-items: center;
  max-width: 960px;
  width: 100%;
  position: relative;
  z-index: 10;
}

/* 左侧品牌 */
.brand-side {
  flex: 1;
  animation: slideInLeft 0.7s cubic-bezier(0.4,0,0.2,1);
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 32px;
}
.logo-icon { font-size: 28px; }
.logo-name {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--accent);
}
.brand-title {
  font-family: var(--font-display);
  font-size: 52px;
  line-height: 1.15;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 20px;
}
.brand-title em {
  font-style: italic;
  color: var(--coral);
}
.brand-desc {
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.7;
  max-width: 320px;
  margin-bottom: 40px;
}
.brand-stats {
  display: flex;
  gap: 32px;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat-num {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

/* 右侧表单 */
.form-side {
  width: 400px;
  flex-shrink: 0;
  animation: slideInRight 0.7s cubic-bezier(0.4,0,0.2,1);
}
.form-card {
  padding: 40px;
}
.form-header {
  margin-bottom: 28px;
}
.form-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.form-sub {
  color: var(--text-secondary);
  font-size: 14px;
}
.submit-btn {
  width: 100%;
  height: 52px !important;
  border-radius: var(--radius-sm) !important;
  font-size: 15px !important;
  margin-top: 8px;
}
.divider {
  text-align: center;
  margin: 20px 0;
  color: var(--text-muted);
  font-size: 13px;
  position: relative;
}
.divider::before, .divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 30%;
  height: 1px;
  background: var(--border);
}
.divider::before { left: 0; }
.divider::after { right: 0; }

.register-btn {
  width: 100%;
  height: 48px !important;
  border-radius: var(--radius-sm) !important;
  font-size: 14px !important;
}
.footnote {
  text-align: center;
  margin-top: 20px;
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 0.06em;
}

@keyframes drift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.05); }
  66% { transform: translate(-15px, 20px) scale(0.95); }
}
@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-32px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes slideInRight {
  from { opacity: 0; transform: translateX(32px); }
  to { opacity: 1; transform: translateX(0); }
}

@media (max-width: 768px) {
  .brand-side { display: none; }
  .form-side { width: 100%; }
}
</style>