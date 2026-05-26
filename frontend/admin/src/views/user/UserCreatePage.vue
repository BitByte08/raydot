<template>
  <div class="page">
    <h1>사용자 생성</h1>
    <form @submit.prevent="submit" class="form">
      <div class="field"><label>학번</label><input v-model="form.student_id" required /></div>
      <div class="field"><label>이름</label><input v-model="form.name" required /></div>
      <div class="field"><label>이메일</label><input v-model="form.email" type="email" required /></div>
      <div class="field"><label>초기 PIN (선택)</label><input v-model="form.pin" maxlength="4" pattern="\d{4}" placeholder="4자리 숫자" /></div>
      <p v-if="msg" :class="ok ? 'ok' : 'err'">{{ msg }}</p>
      <div class="btns">
        <router-link to="/users" class="cancel">취소</router-link>
        <button type="submit" class="submit" :disabled="loading">{{ loading ? '생성 중...' : '생성' }}</button>
      </div>
    </form>
  </div>
</template>
<script setup>
import { ref, reactive } from 'vue'; import { useRouter } from 'vue-router'; import apiClient from '@/services/api'
const router = useRouter(); const form = reactive({ student_id: '', name: '', email: '', pin: '' })
const loading = ref(false); const msg = ref(''); const ok = ref(false)
async function submit() {
  loading.value = true; msg.value = ''
  try { await apiClient.post('/api/admin/user/create', form); ok.value = true; msg.value = '사용자가 생성되었습니다'; setTimeout(() => router.push('/users'), 1000) }
  catch(e) { ok.value = false; msg.value = e.response?.data?.detail || '생성 실패' }
  finally { loading.value = false }
}
</script>
<style scoped>
.page { max-width: 600px; }
h1 { font-size: 24px; margin-bottom: 20px; }
.form { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 600; color: #666; margin-bottom: 4px; }
.btns { display: flex; gap: 12px; margin-top: 20px; }
.cancel { padding: 10px 20px; background: #f0f0f5; color: #666; border-radius: 6px; text-decoration: none; }
.submit { padding: 10px 20px; background: #4361ee; color: #fff; border-radius: 6px; }
.submit:disabled { background: #ccc; }
.ok { color: #2ecc71; }
.err { color: #e74c3c; }
</style>
