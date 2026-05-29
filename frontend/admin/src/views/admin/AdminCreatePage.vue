<template>
  <div class="page">
    <h1>관리자 추가</h1>
    <form @submit.prevent="submit" class="form">
      <div class="field"><label>학교 이메일</label><input v-model="form.email" type="email" :placeholder="'@' + schoolDomain" required /></div>
      <div class="field"><label>이름</label><input v-model="form.name" placeholder="관리자 이름" /></div>
      <div class="field"><label>비밀번호</label><input v-model="form.password" type="password" minlength="8" required /></div>
      <div class="field"><label>역할</label>
        <select v-model="form.role">
          <option value="staff">staff</option>
          <option value="manager">manager</option>
          <option value="superadmin">superadmin</option>
        </select>
      </div>
      <div class="field"><label>키오스크 PIN (선택)</label><input v-model="form.pin" maxlength="4" pattern="\d{4}" placeholder="4자리 숫자, 비워두면 미설정" /></div>
      <p v-if="msg" :class="ok ? 'ok' : 'err'">{{ msg }}</p>
      <div class="btns">
        <router-link to="/admins" class="cancel">취소</router-link>
        <button type="submit" class="submit" :disabled="loading">{{ loading ? '생성 중...' : '생성' }}</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/services/api'

const router = useRouter()
const schoolDomain = 'school.edu'
const form = reactive({ email: '', name: '', password: '', role: 'staff', pin: '' })
const loading = ref(false)
const msg = ref('')
const ok = ref(false)

async function submit() {
  loading.value = true; msg.value = ''
  try {
    const body = { email: form.email, name: form.name, password: form.password, role: form.role }
    if (form.pin) body.pin = form.pin
    await apiClient.post('/api/admin/admins', body)
    ok.value = true; msg.value = '관리자가 생성되었습니다'
    setTimeout(() => router.push('/admins'), 800)
  } catch (e) {
    ok.value = false
    msg.value = e.response?.data?.detail || '생성 실패'
  } finally { loading.value = false }
}
</script>

<style scoped>
.page { max-width: 600px; }
h1 { font-size: 24px; margin-bottom: 20px; }
.form { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 600; color: #666; margin-bottom: 4px; }
.field input, .field select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.btns { display: flex; gap: 12px; margin-top: 20px; }
.cancel { padding: 10px 20px; background: #f0f0f5; color: #666; border-radius: 6px; text-decoration: none; }
.submit { padding: 10px 20px; background: #4361ee; color: #fff; border-radius: 6px; }
.submit:disabled { background: #ccc; }
.ok { color: #2ecc71; }
.err { color: #e74c3c; }
</style>
