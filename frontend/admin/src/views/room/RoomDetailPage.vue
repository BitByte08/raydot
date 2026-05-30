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
      <div>
        <button class="qr-btn" @click="toggleDoorQR">Door QR 발급</button>
        <div v-if="showDoorQR" class="qr-box">
          <p>ESP32에서 이 QR을 스캔하거나 수동 입력하세요</p>
          <canvas ref="doorQRCanvas" width="200" height="200"></canvas>
          <div class="door-qr-text">ROOM:{{ code }}</div>
        </div>
      </div>
      <div class="reg-row" style="margin-top:12px">
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
      <div class="layout-controls">
        <label>열(cols) <input v-model.number="layout.cols" type="number" min="1" max="20" /></label>
        <label>행(rows) <input v-model.number="layout.rows" type="number" min="1" max="20" /></label>
        <button class="save-btn" @click="saveLayout" :disabled="saving">{{ saving ? '저장 중...' : '레이아웃 저장' }}</button>
      </div>
      <p v-if="layoutMsg" :class="layoutOk ? 'ok' : 'err'">{{ layoutMsg }}</p>
      <div class="layout-grid" :style="{ gridTemplateColumns: `repeat(${layout.cols}, 1fr)` }">
        <div v-for="cell in cells" :key="`${cell.x}-${cell.y}`"
          class="layout-cell"
          :class="{
            occupied: cell.seat && !cell.seat.disabled,
            disabled: cell.seat?.disabled,
            empty: !cell.seat,
          }"
          @click="onCellClick(cell)">
          <span v-if="cell.seat" class="seat-num">{{ cell.seat.number }}</span>
          <span v-if="cell.seat?.disabled" class="seat-badge">X</span>
          <span v-else-if="!cell.seat" class="plus-hint">+</span>
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
import { ref, computed, onMounted, reactive, nextTick, watch } from 'vue'; import { useRoute } from 'vue-router'; import apiClient from '@/services/api'
import QRCode from 'qrcode'

const route = useRoute(); const code = route.params.code
const room = ref(null); const seats = ref([]); const doorLogs = ref([])
const kioskId = ref(''); const doorId = ref(''); const showDoorQR = ref(false)
const doorQRCanvas = ref(null)

function toggleDoorQR() {
  showDoorQR.value = !showDoorQR.value
  if (showDoorQR.value) {
    nextTick(() => {
      if (doorQRCanvas.value) {
        QRCode.toCanvas(doorQRCanvas.value, `ROOM:${code}`, { width: 200, margin: 2 })
      }
    })
  }
}

async function load() {
  try {
    const [r, s, d] = await Promise.all([
      apiClient.get(`/api/admin/room/${code}`),
      apiClient.get(`/api/room/${code}/seats`),
      apiClient.get(`/api/admin/room/${code}/door/logs`),
    ])
    room.value = r.data
    seats.value = s.data.seats || s.data
    doorLogs.value = d.data
  } catch (e) { /* handled by router guards */ }
}

async function regKiosk() {
  if (!kioskId.value) return
  await apiClient.post(`/api/admin/room/${code}/kiosk/register`, { kiosk_id: kioskId.value })
  kioskId.value = ''
  await load()
}

async function regDoor() {
  if (!doorId.value) return
  await apiClient.post(`/api/admin/room/${code}/door/register`, { door_id: doorId.value })
  doorId.value = ''
  await load()
}

async function doorCmd(cmd) {
  await apiClient.post(`/api/room/${code}/door/command`, { command: cmd })
  await load()
}
const layout = reactive({ cols: 5, rows: 4 })
const saving = ref(false)
const layoutMsg = ref('')
const layoutOk = ref(false)

function fmt(iso) { return iso ? new Date(iso).toLocaleString('ko-KR') : '' }

const cells = computed(() => {
  const map = {}
  for (const s of seats.value) {
    const x = s.pos_x ?? 0; const y = s.pos_y ?? 0
    map[`${x}-${y}`] = s
  }
  const result = []
  for (let y = 0; y < layout.rows; y++) {
    for (let x = 0; x < layout.cols; x++) {
      result.push({ x, y, seat: map[`${x}-${y}`] || null })
    }
  }
  return result
})

function onCellClick(cell) {
  if (cell.seat) {
    cell.seat.disabled = !cell.seat.disabled
  } else {
    const existing = cells.value.filter(c => c.seat)
    const n = existing.length + 1
    const number = `${String.fromCharCode(65 + cell.y)}${String(cell.x + 1).padStart(2, '0')}`
    cell.seat = { id: -n, number, pos_x: cell.x, pos_y: cell.y, disabled: false, status: 'empty', user_id: null, user_name: null }
    seats.value.push(cell.seat)
  }
}

async function saveLayout() {
  const occupied = seats.value.filter(s => s.status === 'occupied')
  if (occupied.length > 0) {
    if (!confirm(`${occupied.length}개 좌석이 사용 중입니다. 레이아웃을 변경하면 퇴실 처리됩니다. 계속하시겠습니까?`)) return
    for (const s of occupied) {
      try { await apiClient.post(`/api/room/${code}/check-out`, { seat_id: s.id, user_id: s.user_id }) } catch(e) { /* best-effort */ }
    }
  }
  saving.value = true; layoutMsg.value = ''
  const payload = { seats: seats.value.map(s => ({ number: s.number, enabled: !s.disabled, pos_x: s.pos_x, pos_y: s.pos_y })) }
  try {
    await apiClient.put(`/api/admin/room/${code}/seats`, payload)
    layoutOk.value = true; layoutMsg.value = '레이아웃이 저장되었습니다'
    await load()
  } catch (e) {
    layoutOk.value = false; layoutMsg.value = e.response?.data?.detail || '저장 실패'
  } finally { saving.value = false }
}
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
.qr-btn { padding: 8px 16px; background: #8e44ad; color: #fff; border-radius: 6px; font-size: 14px; }
.qr-box { background: #f8f0ff; border: 2px dashed #8e44ad; border-radius: 8px; padding: 16px; margin-top: 8px; text-align: center; }
.qr-box p { font-size: 13px; color: #666; margin-bottom: 8px; }
.door-qr-text { font-size: 28px; font-weight: bold; color: #1a1a2e; font-family: monospace; letter-spacing: 2px; }

.layout-controls { display: flex; gap: 16px; align-items: flex-end; margin-bottom: 12px; }
.layout-controls label { font-size: 14px; color: #666; display: flex; flex-direction: column; gap: 4px; }
.layout-controls input { width: 70px; padding: 6px; border: 1px solid #ddd; border-radius: 4px; text-align: center; font-size: 16px; }
.save-btn { padding: 8px 16px; background: #2ecc71; color: #fff; border-radius: 6px; font-size: 14px; margin-left: auto; }
.save-btn:disabled { background: #ccc; }
.ok { color: #2ecc71; font-size: 13px; margin-top: 4px; }
.err { color: #e74c3c; font-size: 13px; margin-top: 4px; }

.layout-grid { display: grid; gap: 6px; background: #f0f0f5; padding: 8px; border-radius: 6px; }
.layout-cell { aspect-ratio: 1; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; font-size: 14px; font-weight: bold; min-height: 56px; transition: all 0.15s; }
.layout-cell.empty { background: #e8e8ec; color: #ccc; }
.layout-cell.empty:hover { background: #d0d0d8; color: #999; }
.layout-cell.occupied { background: #d4edda; color: #155724; border: 2px solid #2ecc71; }
.layout-cell.occupied:hover { background: #c3e6cb; }
.layout-cell.disabled { background: #f8d7da; color: #721c24; border: 2px dashed #e74c3c; }
.layout-cell.disabled:hover { background: #f5c6cb; }
.seat-num { font-size: 15px; letter-spacing: 0.5px; }
.seat-badge { font-size: 11px; margin-top: 2px; opacity: 0.8; }
.plus-hint { font-size: 24px; opacity: 0.3; }
</style>
