<template>
  <div class="desk-screen">
    <div class="top-bar">
      <span class="greeting" @click="$router.push('/user/info')">{{ authStore.user?.name }}님</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRoomStore } from '@/stores/room'
import apiClient from '@/services/api'
import { connectMqtt, onMessage, disconnectMqtt, TOPICS } from '@/services/mqtt'

const router = useRouter()
const authStore = useAuthStore()
const roomStore = useRoomStore()
const showMenu = ref(false)

function seatClass(seat) {
  if (seat.status === 'disabled') return 'disabled'
  if (seat.status === 'occupied') {
    if (seat.user_id === authStore.user?.id) return 'my-seat'
    return 'occupied'
  }
  return 'empty'
}

function onSeatClick(seat) {
  if (seat.status === 'disabled') return
  if (seat.status === 'occupied' && seat.user_id === authStore.user?.id) {
    router.push({ name: 'check-out', query: { sid: seat.id, snum: seat.number } })
  } else if (seat.status === 'empty') {
    router.push({ name: 'check-in', query: { sid: seat.id, snum: seat.number } })
  }
}

function doLogout() { authStore.logout(); router.push('/') }

onMounted(async () => {
  if (!authStore.isLoggedIn) { router.push('/'); return }
  try {
    const { data } = await apiClient.get('/api/rooms')
    if (data.length > 0) {
      roomStore.setRoom(data[0].code, data[0].name)
      const r = await apiClient.get(`/api/room/${data[0].code}/seats`)
      roomStore.setSeats(r.data.seats)

      // Connect MQTT for real-time seat state updates
      connectMqtt(data[0].code)
      // Auto-register kiosk with room
      apiClient.post(`/api/room/${data[0].code}/kiosk/register`, { kiosk_id: `kiosk-${data[0].code}` }).catch(() => {})
      onMessage((topic, payload) => {
        const code = roomStore.roomCode
        if (topic === TOPICS.seatState(code) && payload.seat_id) {
          roomStore.updateSeat(payload.seat_id, payload.status, payload.user_id, payload.user_name)
        }
      })
    }
  } catch(e) { console.error('Failed to load seats:', e) }
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
.seat-card.my-seat { background: #2ecc71; color: #fff; }
.seat-card.disabled { background: #e74c3c; opacity: 0.5; }
.seat-num { font-size: 18px; font-weight: bold; }
.seat-user { font-size: 11px; margin-top: 2px; opacity: 0.9; }
.menu-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 50; }
.menu { position: absolute; right: 0; top: 0; bottom: 0; width: 220px; background: #fff; display: flex; flex-direction: column; padding: 60px 0 0; }
.menu button { padding: 14px 20px; background: none; border-radius: 0; font-size: 16px; text-align: left; border-bottom: 1px solid #eee; }
.menu button:active { background: #f0f0f5; }
.menu .logout { color: #e74c3c; margin-top: auto; border-top: 1px solid #eee; }
</style>
