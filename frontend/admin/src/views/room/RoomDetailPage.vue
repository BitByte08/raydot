<template>
  <div class="page" v-if="room">
    <div class="top"><h1>{{ room.name }}</h1><router-link to="/rooms">← 목록</router-link></div>
    
    <div class="section">
      <h2>키오스크 연결</h2>
      <div class="reg-row">
        <input v-model="kioskId" placeholder="키오스크 ID" />
        <button @click="regKiosk">연결</button>
        <span class="status" :class="room.kiosk_id ? 'on' : 'off'">{{ room.kiosk_id ? `연결됨 (${room.kiosk_id})` : '미연결' }}</span>
      </div>
    </div>

    <div class="section">
      <h2>출입문 연결</h2>
      <div v-if="code" class="qr-hint">
        <button class="qr-btn" @click="showDoorQR = !showDoorQR">Door QR 발급</button>
        <div v-if="showDoorQR" class="qr-box">
          <p>ESP32에서 이 QR을 스캔하세요</p>
          <canvas ref="doorQRCanvas" class="door-qr"></canvas>
          <p class="qr-code-text">ROOM:{{ code }}</p>
        </div>
      </div>
      <div class="reg-row">
        <input v-model="doorId" placeholder="출입문 ID" />
        <button @click="regDoor">연결</button>
        <span class="status" :class="room.door_id ? 'on' : 'off'">{{ room.door_id ? `연결됨 (${room.door_id})` : '미연결' }}</span>
      </div>
      <div v-if="room.door_id" class="door-controls">
        <button class="open-btn" @click="doorCmd('open')">열기</button>
        <button class="close-btn" @click="doorCmd('close')">닫기</button>
      </div>
    </div>

    <div class="section">
      <h2>좌석 배치</h2>
      <div class="seat-grid">
        <div v-for="s in seats" :key="s.id" class="seat" :class="{ disabled: s.disabled }">
          <span class="num">{{ s.number }}</span>
          <button class="toggle" @click="toggleSeat(s)">{{ s.disabled ? '활성화' : '비활성화' }}</button>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>출입문 기록</h2>
      <table>
        <thead><tr><th>시간</th><th>이벤트</th><th>사용자</th></tr></thead>
        <tbody><tr v-for="l in doorLogs" :key="l.time"><td>{{ fmt(l.time) }}</td><td>{{ l.event }}</td><td>{{ l.user_name || '-' }}</td></tr></tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'; import { useRoute } from 'vue-router'; import apiClient from '@/services/api'
const route = useRoute(); const code = route.params.code
const room = ref(null); const seats = ref([]); const doorLogs = ref([])
const kioskId = ref(''); const doorId = ref('')
function fmt(iso) { return iso ? new Date(iso).toLocaleString('ko-KR') : '' }
async function load() {
  const { data: r } = await apiClient.get('/api/admin/rooms'); room.value = r.find(x => x.code === code)
  if (!room.value) return
  const { data: s } = await apiClient.get(`/api/room/${code}/seats`); seats.value = s.seats
  const { data: l } = await apiClient.get(`/api/admin/room/${code}/door/logs`); doorLogs.value = l
}
async function regKiosk() { await apiClient.post(`/api/admin/room/${code}/kiosk/register`, { kiosk_id: kioskId.value }); await load() }
async function regDoor() { await apiClient.post(`/api/admin/room/${code}/door/register`, { door_id: doorId.value }); await load() }
async function doorCmd(cmd) { await apiClient.post(`/api/room/${code}/door/command`, { command: cmd }) }
async function toggleSeat(s) { await apiClient.put(`/api/admin/room/${code}/seat/${s.id}/disable`, { disabled: !s.disabled }); await load() }
onMounted(load)
</script>
<style scoped>
.page { max-width: 1000px; }
h1 { font-size: 24px; }
h2 { font-size: 18px; margin-bottom: 12px; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.top a { color: #4361ee; }
.section { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.reg-row { display: flex; gap: 8px; align-items: center; }
.reg-row input { max-width: 200px; }
.reg-row button { padding: 8px 16px; background: #4361ee; color: #fff; border-radius: 6px; }
.status { font-size: 14px; margin-left: 8px; }
.status.on { color: #2ecc71; }
.status.off { color: #e74c3c; }
.door-controls { display: flex; gap: 8px; margin-top: 12px; }
.open-btn { padding: 8px 16px; background: #2ecc71; color: #fff; border-radius: 6px; }
.close-btn { padding: 8px 16px; background: #e74c3c; color: #fff; border-radius: 6px; }
.seat-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.seat { background: #f0f0f5; border-radius: 6px; padding: 12px; text-align: center; }
.seat.disabled { background: #ffe0e0; }
.num { font-size: 16px; font-weight: bold; }
.toggle { font-size: 12px; padding: 4px 8px; margin-top: 4px; background: #fff; border-radius: 4px; }
</style>
