export interface RegisterRequest {
  username: string
  password: string
  name: string
  age: number
  weight_kg: number
  height_cm: number
  goal: 'lose_fat' | 'build_muscle' | 'maintain'
  activity_level: 'sedentary' | 'light' | 'moderate' | 'active'
  dietary_pref: 'no restriction' | 'vegetarian' | 'vegan' | 'low_carb'
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CheckinRequest {
  weight_kg: number
  steps: number
  calories_intake: number
  workout_done: boolean
  mood: 'good' | 'neutral' | 'tired'
}

export interface CheckinResponse {
  date: string
  mode: string
  workout_plan: string
  diet_plan: string
  trend_summary: string
  motivation_message: string
}

export interface DailyLogItem {
  date: string
  weight_kg: number | null
  steps: number | null
  calories_intake: number | null
  workout_done: boolean | null
  mood: string | null
}

export interface UserProfile {
  name: string
  age: number
  weight_kg: number
  height_cm: number
  goal: string
  activity_level: string
  dietary_pref: string
}

// ── 小助手 ──────────────────────────────────────────────

export interface AssistantDirectives {
  mode?: 'conservative' | 'normal' | 'aggressive' | null
  workout_focus?: string
  workout_avoid?: string
  diet_adjustments?: string
  general_notes?: string
}

export interface AssistantChatRequest {
  message: string
  current_plan?: Record<string, unknown> | null
}

export interface AssistantChatResponse {
  reply: string
  directives?: AssistantDirectives | null
  preferences_updated: boolean
}

export interface AssistantHistoryItem {
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

// ── 重新生成 ──────────────────────────────────────────────

export interface RegenerateRequest {
  weight_kg: number
  steps: number
  calories_intake: number
  workout_done: boolean
  mood: 'good' | 'neutral' | 'tired'
  directives?: AssistantDirectives | null
}