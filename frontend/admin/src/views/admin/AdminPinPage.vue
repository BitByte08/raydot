<template>
  <div class="page">
    <h1>내 키오스크 PIN 설정</h1>
    <p class="hint">키오스크의 WiFi 설정 등 관리자 화면을 잠금 해제할 때 사용하는 4자리 PIN입니다.</p>
    <form @submit.prevent="submit" class="form">
      <div class="field">
        <label>새 PIN (4자리 숫자)</label>
        <input v-model="pin" maxlength="4" inputmode="numeric" pattern="\d{4}" placeholder="••••" required />
      </div>
      <div class="field">
        <label>PIN 확인</label>
        <input v-model="pinConfirm" maxlength="4" inputmode="numeric" pattern="\d{4}" placeholder="••••" required />
      </div>
      <p v-if="msg" :class="ok ? 'ok' : 'err'">{{ msg }}</p>
      <div class="btns">
        <router-link to="/admins" class="cancel">취소</router-link>
        <button type="submit" class="submit" :disabled="loading">{{ loading ? '저장 중...' : '저장' }}</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import apiClient from '@/services/api'

const pin = ref('')
const pinConfirm = ref('')
const loading = ref(false)
const msg = ref('')
const ok = ref(false)

async function submit() {
  ok.value = false; msg.value = ''
  if (!/^\d{4}$/.test(pin.value)) { msg.value = 'PIN은 숫자 4자리여야 합니다'; return }
  if (pin.value !== pinConfirm.value) { msg.value = 'PIN이 일치하지 않습니다'; return }
  loading.value = true
  try {
    await apiClient.post('/api/admin/pin', { pin: pin.value })
    ok.value = true; msg.value = 'PIN이 저장되었습니다'
    pin.value = ''; pinConfirm.value = ''
  } catch (e) {
    msg.value = e.response?.data?.detail || '저장 실패'
  } finally { loading.value = false }
}
</script>

<style scoped>
.page { max-width: 520px; }
h1 { font-size: 24px; margin-bottom: 8px; }
.hint { color: #666; font-size: 14px; margin-bottom: 20px; }
.form { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 600; color: #666; margin-bottom: 4px; }
.field input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 20px; letter-spacing: 6px; text-align: center; font-family: monospace; }
.btns { display: flex; gap: 12px; margin-top: 20px; }
.cancel { padding: 10px 20px; background: #f0f0f5; color: #666; border-radius: 6px; text-decoration: none; }
.submit { padding: 10px 20px; background: #4361ee; color: #fff; border-radius: 6px; }
.submit:disabled { background: #ccc; }
.ok { color: #2ecc71; }
.err { color: #e74c3c; }
</style>
