<template>
  <div class="gate-screen">
    <div class="head"><button @click="$router.push('/')">←</button><h2>{{ title }}</h2></div>

    <div v-if="!user" class="gate" @click.self="showKeyboard = false">
      <div class="gate-box" @click.self="showKeyboard = false">
        <p class="gate-title">본인 확인이 필요합니다</p>
        <input v-model="studentId" class="gate-input" type="text"
          placeholder="학번 입력 또는 학생증 스캔"
          @keyup.enter="onIdSubmit" @focus="showKeyboard = true" @click="showKeyboard = true" />
        <button class="gate-btn" :disabled="!studentId" @click="onIdSubmit">다음</button>
        <p v-if="error" class="gate-err">{{ error }}</p>
      </div>
    </div>

    <slot v-else :user="user" :token="token" />

    <PinKeypad v-if="showPinPad" :title="`${studentId} PIN 입력`"
      v-model="pin" @confirm="onPinConfirm" @cancel="showPinPad = false" />
    <VirtualKeyboard v-model="studentId" :visible="showKeyboard && !showPinPad && !user" @close="showKeyboard = false" />

    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p class="loading-text">본인 확인 중...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/services/api'
import PinKeypad from '@/components/PinKeypad.vue'
import VirtualKeyboard from '@/components/VirtualKeyboard.vue'

defineProps({ title: { type: String, required: true } })
const emit = defineEmits(['verified'])

const authStore = useAuthStore()

const user = ref(null)
const token = ref('')
const studentId = ref('')
const pin = ref('')
const showPinPad = ref(false)
const showKeyboard = ref(false)
const error = ref('')
const loading = ref(false)

const scannerBuffer = ref('')
let scannerTimer = null

function onIdSubmit() {
  if (!studentId.value) return
  error.value = ''
  showKeyboard.value = false
  showPinPad.value = true
}

async function onPinConfirm(pinValue) {
  error.value = ''
  loading.value = true
  try {
    const { data } = await apiClient.post('/api/auth/login', {
      student_id: studentId.value,
      pin: pinValue,
    })
    if (data.blacklist) { error.value = '이용이 제한되었습니다'; return }
    if (data.success) {
      user.value = data.user
      token.value = data.token
      authStore.setInfoUser(data.user, data.token)
      showPinPad.value = false
      showKeyboard.value = false
      emit('verified', data.user, data.token)
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '확인 실패'
    showPinPad.value = false
    pin.value = ''
  } finally {
    loading.value = false
  }
}

function handleScannerInput(e) {
  if (user.value || showPinPad.value) return
  clearTimeout(scannerTimer)
  const key = e.key
  if (key === 'Enter') {
    const scanned = scannerBuffer.value.trim()
    if (scanned) { studentId.value = scanned; scannerBuffer.value = ''; onIdSubmit() }
    return
  }
  if (key.length === 1 && /^[\w\-:.]$/.test(key)) scannerBuffer.value += key
  scannerTimer = setTimeout(() => { scannerBuffer.value = '' }, 200)
}

onMounted(() => {
  window.addEventListener('keydown', handleScannerInput)
  if (authStore.infoUser && authStore.infoToken) {
    user.value = authStore.infoUser
    token.value = authStore.infoToken
    emit('verified', authStore.infoUser, authStore.infoToken)
  }
})
onUnmounted(() => window.removeEventListener('keydown', handleScannerInput))
</script>

<style scoped>
.gate-screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.gate { flex: 1; display: flex; align-items: center; justify-content: center; padding: 20px; }
.gate-box { background: #fff; border-radius: 16px; padding: 32px; text-align: center; width: 380px; }
.gate-title { font-size: 16px; color: #666; margin-bottom: 18px; }
.gate-input { width: 300px; text-align: center; font-size: 18px; padding: 10px; border: 2px solid #4361ee; border-radius: 8px; margin-bottom: 14px; }
.gate-btn { width: 200px; padding: 12px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 16px; }
.gate-btn:disabled { background: #ccc; }
.gate-err { color: #e74c3c; margin-top: 12px; font-size: 14px; }
.loading-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 300; }
.spinner { width: 56px; height: 56px; border: 5px solid rgba(255,255,255,0.25); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
.loading-text { margin-top: 14px; color: #fff; font-size: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
