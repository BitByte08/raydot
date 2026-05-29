<template>
  <div class="desk-screen">
    <div class="top-bar">
      <span class="greeting">{{ authStore.user?.name || '좌석을 선택하세요' }}</span>
      <h2>{{ roomStore.roomName || '좌석 현황' }}</h2>
      <div class="top-actions">
        <button class="menu-btn" @click="showMenu = !showMenu">≡</button>
      </div>
    </div>
    <div class="legend">
      <span class="dot empty"></span> 빈좌석
      <span class="dot occupied"></span> 사용중
      <span class="dot disabled"></span> 사용불가
    </div>
    <div class="seat-grid">
      <div v-for="seat in roomStore.seats" :key="seat.id" class="seat-card"
        :class="seatClass(seat)" @click="onSeatClick(seat)">
        <span class="seat-num">{{ seat.number }}</span>
        <span class="seat-user" v-if="seat.status === 'occupied' && seat.user_name">{{ seat.user_name.substring(0,3) }}</span>
      </div>
    </div>

    <!-- 로그인 모달 -->
    <div v-if="showLoginModal" class="modal-overlay" @click.self="onOverlayTap">
      <div class="login-modal">
        <h3>{{ selectedSeat?.number }} 좌석 입실</h3>
        <p class="scan-label">학생증을 스캔해주세요</p>
        <input ref="scanInput" v-model="loginStudentId" class="scan-input" type="text"
          placeholder="또는 학번 직접 입력" @keyup.enter="onScan" @focus="showKeyboard = true" @click="showKeyboard = true" />
        <div class="login-btns">
          <button class="btn-cancel" @click="closeLoginModal">취소</button>
          <button class="btn-confirm" :disabled="!loginStudentId" @click="onScan">확인</button>
        </div>
        <PinKeypad v-if="showPinPad" title="PIN 입력" v-model="loginPin" @confirm="onLogin" @cancel="showPinPad = false" />
        <VirtualKeyboard v-model="loginStudentId" :visible="showKeyboard && !showPinPad" @close="showKeyboard = false" />
        <div v-if="loginError" class="login-error">{{ loginError }}</div>
      </div>
    </div>

    <!-- QR 표시 모달 -->
    <div v-if="showQRModal" class="modal-overlay">
      <div class="qr-modal">
        <h3>입실 완료</h3>
        <canvas ref="qrCanvas" class="qr-canvas"></canvas>
        <p>정독실 입장 시 QR을 스캔하세요</p>
        <p class="qr-expire" v-if="qrExpire">유효시간: {{ qrRemaining }}초</p>
        <button class="btn-ok" @click="closeQR">확인</button>
      </div>
    </div>

    <div v-if="showMenu" class="menu-overlay" @click.self="showMenu = false">
      <div class="menu">
        <button @click="$router.push('/user/info'); showMenu=false">내 정보</button>
        <button @click="$router.push('/user/log'); showMenu=false">이용 기록</button>
        <button @click="$router.push('/board/notify'); showMenu=false">공지사항</button>
        <button @click="$router.push('/board/inquiry'); showMenu=false">문의사항</button>
        <button @click="$router.push('/wifi'); showMenu=false">WiFi 설정</button>
        <button class="logout" @click="doLogout">로그아웃</button>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p class="loading-text">{{ loadingMessage || '처리 중...' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRoomStore } from '@/stores/room'
import apiClient from '@/services/api'
import { connectMqtt, onMessage, disconnectMqtt, TOPICS } from '@/services/mqtt'
import PinKeypad from '@/components/PinKeypad.vue'
import VirtualKeyboard from '@/components/VirtualKeyboard.vue'
import QRCode from 'qrcode'

const router = useRouter()
const authStore = useAuthStore()
const roomStore = useRoomStore()
const showMenu = ref(false)

// Login modal state
const showLoginModal = ref(false)
const selectedSeat = ref(null)
const scanInput = ref(null)
const loginStudentId = ref('')
const loginPin = ref('')
const showPinPad = ref(false)
const showKeyboard = ref(false)
const loginError = ref('')
const scannerBuffer = ref('')
let scannerTimer = null

// QR modal state
const showQRModal = ref(false)
const qrCanvas = ref(null)
const qrExpire = ref(null)
const qrRemaining = ref(30)
let qrTimer = null

const loading = ref(false)
const loadingMessage = ref('')

function seatClass(seat) {
  if (seat.status === 'disabled') return 'disabled'
  if (seat.status === 'occupied') return 'occupied'
  return 'empty'
}

function onSeatClick(seat) {
  if (seat.status === 'disabled') return
  if (seat.status === 'occupied') return
  selectedSeat.value = seat
  loginStudentId.value = ''
  loginPin.value = ''
  loginError.value = ''
  showKeyboard.value = false
  showLoginModal.value = true
}

function closeLoginModal() {
  showLoginModal.value = false
  showPinPad.value = false
  showKeyboard.value = false
  selectedSeat.value = null
  loginStudentId.value = ''
  loginPin.value = ''
}

function onOverlayTap() {
  if (showKeyboard.value) { showKeyboard.value = false; return }
  if (showPinPad.value) { showPinPad.value = false; return }
  closeLoginModal()
}

function onScan() {
  if (!loginStudentId.value) return
  showPinPad.value = true
}

async function onLogin(pinValue) {
  loginError.value = ''
  loading.value = true
  loadingMessage.value = '로그인 중...'
  try {
    const { data } = await apiClient.post('/api/auth/login', { student_id: loginStudentId.value, pin: pinValue })
    if (data.blacklist) { loginError.value = '이용이 제한되었습니다'; loading.value = false; return }
    if (data.success) {
      authStore.setUser(data.user, data.token)
      showPinPad.value = false
      showKeyboard.value = false
      loadingMessage.value = '입실 처리 중...'
      await doCheckIn()
    }
  } catch (e) {
    loginError.value = e.response?.data?.detail || '로그인 실패'
    showPinPad.value = false; loginPin.value = ''
  } finally {
    loading.value = false
  }
}

async function doCheckIn() {
  const code = roomStore.roomCode
  if (!code) { loginError.value = '정독실 정보 오류'; return }
  const seat = selectedSeat.value
  try {
    const { data } = await apiClient.post(`/api/room/${code}/check-in`, {
      seat_id: Number(seat.id),
      user_id: authStore.user?.id,
      pass_type: 'daily',
    })
    if (data.success) {
      roomStore.updateSeat(seat.id, 'occupied', authStore.user?.id, authStore.user?.name)
      showLoginModal.value = false
      showQRModal.value = true
      nextTick(async () => {
        if (qrCanvas.value) {
          await QRCode.toCanvas(qrCanvas.value, data.qr_code, { width: 180, margin: 2 })
        }
      })
      // Countdown
      if (data.expires_at) {
        qrExpire.value = new Date(data.expires_at)
        qrTimer = setInterval(() => {
          const diff = Math.max(0, Math.floor((qrExpire.value - new Date()) / 1000))
          qrRemaining.value = diff
          if (diff <= 0) closeQR()
        }, 1000)
      }
    }
  } catch (e) {
    loginError.value = e.response?.data?.detail || '입실 실패'
  }
}

function closeQR() {
  if (qrTimer) clearInterval(qrTimer)
  showQRModal.value = false
  authStore.logout()
  selectedSeat.value = null
}

function doLogout() { authStore.logout(); router.push('/') }

// Scanner handler
function handleScannerInput(e) {
  if (!showLoginModal.value || showPinPad.value) return
  clearTimeout(scannerTimer)
  const key = e.key
  if (key === 'Enter') {
    const scanned = scannerBuffer.value.trim()
    if (scanned) { loginStudentId.value = scanned; scannerBuffer.value = ''; onScan() }
    return
  }
  if (key.length === 1 && /^[\w\-:.]$/.test(key)) scannerBuffer.value += key
  scannerTimer = setTimeout(() => { scannerBuffer.value = '' }, 200)
}

onMounted(async () => {
  try {
    const { data } = await apiClient.get('/api/rooms')
    if (data.length > 0) {
      roomStore.setRoom(data[0].code, data[0].name)
      const r = await apiClient.get(`/api/room/${data[0].code}/seats`)
      roomStore.setSeats(r.data.seats)
      connectMqtt(data[0].code)
      apiClient.post(`/api/room/${data[0].code}/kiosk/register`, { kiosk_id: `kiosk-${data[0].code}` }).catch(() => {})
      onMessage((topic, payload) => {
        const code = roomStore.roomCode
        if (topic === TOPICS.seatState(code) && payload.seat_id) {
          roomStore.updateSeat(payload.seat_id, payload.status, payload.user_id, payload.user_name)
        }
      })
    }
  } catch(e) { console.error('Failed:', e) }
  window.addEventListener('keydown', handleScannerInput)
})

onUnmounted(() => {
  if (qrTimer) clearInterval(qrTimer)
  window.removeEventListener('keydown', handleScannerInput)
})
</script>

<style scoped>
.desk-screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.top-bar { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.greeting { font-size: 13px; opacity: 0.8; min-width: 60px; cursor: pointer; }
.top-bar h2 { flex: 1; text-align: center; font-size: 18px; }
.menu-btn { background: none; color: #fff; font-size: 22px; }
.legend { display: flex; gap: 12px; padding: 8px 12px; font-size: 13px; background: #fff; }
.dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.dot.empty { background: #bdc3c7; }
.dot.occupied { background: #3498db; }
.dot.disabled { background: #e74c3c; }
.seat-grid { flex: 1; display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; padding: 12px; overflow-y: auto; align-content: start; }
.seat-card { background: #bdc3c7; border-radius: 8px; padding: 14px 8px; text-align: center; cursor: pointer; min-height: 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: all 0.2s; }
.seat-card:active { transform: scale(0.95); }
.seat-card.empty { background: #bdc3c7; }
.seat-card.occupied { background: #3498db; color: #fff; }
.seat-card.disabled { background: #e74c3c; opacity: 0.5; }
.seat-num { font-size: 18px; font-weight: bold; }
.seat-user { font-size: 11px; margin-top: 2px; opacity: 0.9; }

/* Login modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.login-modal { background: #fff; border-radius: 16px; padding: 28px; text-align: center; width: 360px; }
.login-modal h3 { font-size: 22px; margin-bottom: 8px; }
.scan-label { color: #666; font-size: 15px; margin-bottom: 16px; }
.scan-input { width: 280px; text-align: center; font-size: 18px; padding: 8px; border: 2px solid #4361ee; border-radius: 8px; margin-bottom: 16px; }
.login-btns { display: flex; gap: 12px; justify-content: center; }
.login-btns button { padding: 10px 32px; border-radius: 8px; font-size: 16px; }
.btn-cancel { background: #f0f0f5; color: #666; }
.btn-confirm { background: #4361ee; color: #fff; }
.btn-confirm:disabled { background: #ccc; }
.login-error { color: #e74c3c; margin-top: 12px; font-size: 14px; }

/* QR modal */
.qr-modal { background: #fff; border-radius: 16px; padding: 28px; text-align: center; width: 340px; }
.qr-modal h3 { font-size: 22px; margin-bottom: 12px; color: #2ecc71; }
.qr-canvas { margin: 0 auto 12px; }
.qr-modal p { font-size: 15px; color: #333; margin-bottom: 4px; }
.qr-expire { color: #e74c3c !important; font-weight: bold; }
.btn-ok { width: 200px; padding: 12px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 16px; margin-top: 12px; }

.menu-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 50; }
.menu { position: absolute; right: 0; top: 0; bottom: 0; width: 220px; background: #fff; display: flex; flex-direction: column; padding: 60px 0 0; }
.menu button { padding: 14px 20px; background: none; border-radius: 0; font-size: 16px; text-align: left; border-bottom: 1px solid #eee; }
.menu button:active { background: #f0f0f5; }
.menu .logout { color: #e74c3c; margin-top: auto; border-top: 1px solid #eee; }

.loading-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 300; }
.spinner { width: 56px; height: 56px; border: 5px solid rgba(255,255,255,0.25); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
.loading-text { margin-top: 14px; color: #fff; font-size: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
