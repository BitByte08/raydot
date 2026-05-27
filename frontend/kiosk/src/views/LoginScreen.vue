<template>
  <div class="login-screen">
    <div class="login-header">
      <button class="wifi-btn" @click="goWifi">WiFi</button>
      <h2>정독실 입실</h2>
    </div>
    <div class="login-body">
      <div class="scan-area">
        <div class="scan-icon">카드</div>
        <p class="scan-text">학생증을 스캔해주세요</p>
        <input ref="scanInput" v-model="studentId" class="scan-input" type="text" placeholder="또는 학번 직접 입력"
          @keyup.enter="onScan" @focus="showKeyboard = true" @blur="onBlur" />
      </div>
      <button class="btn-submit" :disabled="!studentId" @click="onScan">확인</button>
    </div>
    <PinKeypad v-if="showPinPad" title="PIN 입력" v-model="pin" @confirm="onLogin" @cancel="showPinPad = false" />
    <VirtualKeyboard v-model="studentId" :visible="showKeyboard && !showPinPad" @close="showKeyboard = false" />
    <div v-if="errorMsg" class="error-toast">{{ errorMsg }}</div>
    <div v-if="loading" class="loading-overlay"><div class="spinner"></div></div>
    <div v-if="blacklistAlert" class="blacklist-overlay">
      <div class="blacklist-card">
        <h3>이용 제한</h3>
        <p>정독실 이용이 제한되었습니다.<br/>관리자에게 문의하세요.</p>
        <button class="btn" @click="blacklistAlert = false; studentId=''; pin=''">확인</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/services/api'
import PinKeypad from '@/components/PinKeypad.vue'
import VirtualKeyboard from '@/components/VirtualKeyboard.vue'

const router = useRouter()
const authStore = useAuthStore()

const scanInput = ref(null)
const studentId = ref('')
const pin = ref('')
const showPinPad = ref(false)
const showKeyboard = ref(false)
const errorMsg = ref('')
const loading = ref(false)
const blacklistAlert = ref(false)
const scannerBuffer = ref('')

let scannerTimer = null

function onScan() {
  if (!studentId.value) return
  showPinPad.value = true
}

async function onLogin(pinValue) {
  loading.value = true; errorMsg.value = ''
  try {
    const { data } = await apiClient.post('/api/auth/login', { student_id: studentId.value, pin: pinValue })
    if (data.blacklist) { blacklistAlert.value = true; showPinPad.value = false; return }
    if (data.success) {
      authStore.setUser(data.user, data.token)
      router.push('/desk')
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '로그인 실패'
    showPinPad.value = false; pin.value = ''
  } finally { loading.value = false }
}

function goWifi() { router.push('/wifi') }
function onBlur() { setTimeout(() => { showKeyboard.value = false }, 200) }

// USB RFID/Barcode scanner input handler (keyboard wedge mode)
function handleScannerInput(e) {
  if (showPinPad.value || blacklistAlert.value) return
  clearTimeout(scannerTimer)
  const key = e.key
  if (key === 'Enter') {
    const scanned = scannerBuffer.value.trim()
    if (scanned) { studentId.value = scanned; scannerBuffer.value = ''; onScan() }
    return
  }
  if (key.length === 1 && /^[\w\-:.]$/.test(key)) scannerBuffer.value += key
  scannerTimer = setTimeout(() => { scannerBuffer.value = '' }, 200)
}

onMounted(() => { window.addEventListener('keydown', handleScannerInput) })
onUnmounted(() => { window.removeEventListener('keydown', handleScannerInput) })
</script>

<style scoped>
.login-screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.login-header { display: flex; align-items: center; padding: 12px 16px; background: #1a1a2e; color: #fff; }
.login-header h2 { flex: 1; text-align: center; font-size: 20px; }
.wifi-btn { background: none; color: #fff; font-size: 24px; min-width: 44px; }
.login-body { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; }
.scan-area { text-align: center; margin-bottom: 24px; }
.scan-icon { font-size: 72px; margin-bottom: 12px; }
.scan-text { font-size: 18px; color: #666; margin-bottom: 20px; }
.scan-input { width: 280px; text-align: center; font-size: 18px; }
.btn-submit { width: 200px; padding: 14px; background: #4361ee; color: #fff; font-size: 18px; border-radius: 12px; }
.btn-submit:disabled { background: #ccc; }
.error-toast { position: fixed; top: 12px; left: 50%; transform: translateX(-50%); background: #e74c3c; color: #fff; padding: 10px 24px; border-radius: 8px; font-size: 14px; }
.loading-overlay { position: fixed; top: 0; left: 0; width: 800px; height: 480px; background: rgba(255,255,255,0.7); display: flex; align-items: center; justify-content: center; }
.spinner { width: 40px; height: 40px; border: 4px solid #ddd; border-top-color: #4361ee; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.blacklist-overlay { position: fixed; top: 0; left: 0; width: 800px; height: 480px; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 200; }
.blacklist-card { background: #fff; border-radius: 16px; padding: 32px; text-align: center; max-width: 360px; }
.blacklist-card h3 { color: #e74c3c; font-size: 22px; margin-bottom: 12px; }
.blacklist-card p { color: #666; margin-bottom: 20px; line-height: 1.6; }
.blacklist-card .btn { padding: 12px 32px; background: #4361ee; color: #fff; border-radius: 8px; }
</style>
