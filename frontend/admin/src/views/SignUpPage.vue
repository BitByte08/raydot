<template>
  <div class="signup-page">
    <div class="signup-card">
      <div class="logo">📚 Raydot Admin</div>
      <div class="step" v-if="step === 1">
        <h3>관리자 회원가입</h3>
        <form @submit.prevent="nextStep">
          <div class="field"><label>식별코드</label><input v-model="form.code" placeholder="학교에서 발급받은 코드" required /></div>
          <div class="field"><label>학교 이메일</label><input v-model="form.email" type="email" :placeholder="'@' + schoolDomain" required /></div>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" class="btn" :disabled="loading">{{ loading ? '처리 중...' : '다음' }}</button>
        </form>
      </div>
      <div class="step" v-if="step === 2">
        <h3>비밀번호 설정</h3>
        <form @submit.prevent="doSignUp">
          <div class="field"><label>이름</label><input v-model="form.name" placeholder="관리자 이름" /></div>
          <div class="field"><label>비밀번호</label><input v-model="form.password" type="password" minlength="8" required /></div>
          <div class="field"><label>비밀번호 확인</label><input v-model="form.passwordConfirm" type="password" required /></div>
          <p v-if="pwError" class="error">{{ pwError }}</p>
          <button type="submit" class="btn" :disabled="loading">{{ loading ? '가입 중...' : '회원가입' }}</button>
        </form>
      </div>
      <div v-if="done" class="done">
        <h3>✓ 가입 완료</h3>
        <p>이제 로그인할 수 있습니다.</p>
        <router-link to="/login" class="btn">로그인</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/services/api'

const router = useRouter()
const step = ref(1)
const form = reactive({ code: 'RAYDOT2024', email: '', name: '', password: '', passwordConfirm: '' })
const error = ref('')
const pwError = ref('')
const loading = ref(false)
const done = ref(false)
const schoolDomain = 'school.edu'

function nextStep() {
  error.value = ''
  if (!form.email.endsWith('@' + schoolDomain)) { error.value = '학교 이메일만 사용 가능합니다.'; return }
  step.value = 2
}

async function doSignUp() {
  pwError.value = ''
  if (form.password.length < 8) { pwError.value = '비밀번호는 8자 이상이어야 합니다.'; return }
  if (form.password !== form.passwordConfirm) { pwError.value = '비밀번호가 일치하지 않습니다.'; return }
  loading.value = true
  try {
    await apiClient.post('/api/admin/sign-up', { code: form.code, email: form.email, password: form.password, name: form.name })
    done.value = true
  } catch (e) { pwError.value = e.response?.data?.detail || '회원가입 실패' }
  finally { loading.value = false }
}
</script>

<style scoped>
.signup-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #1a1a2e; }
.signup-card { background: #fff; border-radius: 12px; padding: 40px; width: 420px; box-shadow: 0 4px 24px rgba(0,0,0,0.3); }
.logo { text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 24px; color: #1a1a2e; }
h3 { font-size: 18px; margin-bottom: 20px; color: #333; }
.field { margin-bottom: 14px; }
.field label { display: block; font-size: 13px; font-weight: 600; color: #666; margin-bottom: 4px; }
.field input { width: 100%; }
.error { color: #e74c3c; font-size: 14px; margin-bottom: 12px; }
.btn { width: 100%; padding: 12px; background: #4361ee; color: #fff; border-radius: 6px; font-size: 16px; margin-top: 8px; display: block; text-align: center; text-decoration: none; }
.btn:disabled { background: #ccc; }
.done { text-align: center; }
.done h3 { color: #2ecc71; font-size: 22px; margin-bottom: 8px; }
.done p { color: #666; margin-bottom: 16px; }
</style>
