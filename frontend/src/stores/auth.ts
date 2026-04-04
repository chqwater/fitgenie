import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import type { RegisterRequest, LoginRequest } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))

  const isLoggedIn = computed(() => !!token.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function logout() {
    token.value = null
    localStorage.removeItem('token')
  }

  async function login(data: LoginRequest) {
    const res = await authApi.login(data)
    setToken(res.data.access_token)
  }

  async function register(data: RegisterRequest) {
    const res = await authApi.register(data)
    setToken(res.data.access_token)
  }

  return { token, isLoggedIn, login, register, logout }
})