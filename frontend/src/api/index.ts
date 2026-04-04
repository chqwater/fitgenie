import axios from 'axios'
import type {
  RegisterRequest, LoginRequest, TokenResponse,
  CheckinRequest, CheckinResponse, DailyLogItem, UserProfile
} from './types'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL as string,
  timeout: 60000,
})

// 自动加 token
http.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 跳转登录
http.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  register: (data: RegisterRequest) =>
    http.post<TokenResponse>('/auth/register', data),
  login: (data: LoginRequest) =>
    http.post<TokenResponse>('/auth/login', data),
}

export const dailyApi = {
  checkin: (data: CheckinRequest) =>
    http.post<CheckinResponse>('/daily/checkin', data),
  history: (days = 7) =>
    http.get<DailyLogItem[]>(`/daily/history?days=${days}`),
}

export const profileApi = {
  get: () => http.get<UserProfile>('/profile'),
  update: (data: Partial<UserProfile>) => http.put<UserProfile>('/profile', data),
}
