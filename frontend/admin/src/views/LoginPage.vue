<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">📚 Raydot Admin</div>
      <form @submit.prevent="doLogin">
        <div class="field">
          <label>이메일</label>
          <input v-model="email" type="email" placeholder="admin@school.edu" required />
        </div>
        <div class="field">
          <label>비밀번호</label>
          <input v-model="password" type="password" placeholder="비밀번호" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '로그인 중...' : '로그인' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminAuthStore } from '@/stores/adminAuth'
import apiClient from '@/services/api'

const router = useRouter()
const authStore = useAdminAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function doLogin() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await apiClient.post('/api/admin/login', { email: email.value, password: password.value })
    authStore.setAdmin(data.admin, data.token)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || '로그인 실패'
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #1a1a2e; }
.login-card { background: #fff; border-radius: 12px; padding: 40px; width: 400px; box-shadow: 0 4px 24px rgba(0,0,0,0.3); }
.logo { text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 32px; color: #1a1a2e; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 600; color: #666; margin-bottom: 4px; }
.field input { width: 100%; }
.error { color: #e74c3c; font-size: 14px; margin-bottom: 12px; }
.login-btn { width: 100%; padding: 12px; background: #4361ee; color: #fff; border-radius: 6px; font-size: 16px; margin-top: 8px; }
.login-btn:disabled { background: #ccc; }
</style>
