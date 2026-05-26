<template>
  <div class="dashboard">
    <h1>대시보드</h1>
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-num">{{ stats.totalUsers }}</div><div class="stat-label">전체 사용자</div></div>
      <div class="stat-card warn"><div class="stat-num">{{ stats.blacklistedUsers }}</div><div class="stat-label">이용 제한</div></div>
      <div class="stat-card ok"><div class="stat-num">{{ stats.activeSeats }}</div><div class="stat-label">현재 입실</div></div>
      <div class="stat-card"><div class="stat-num">{{ stats.qrIssuedToday }}</div><div class="stat-label">오늘 QR 발급</div></div>
    </div>

    <div class="section">
      <h2>정독실 현황</h2>
      <div v-for="room in rooms" :key="room.id" class="room-card">
        <div class="room-header">
          <h3>{{ room.name }} ({{ room.code }})</h3>
          <div class="badges">
            <span class="badge" :class="room.kiosk_id ? 'on' : 'off'">키오스크 {{ room.kiosk_id ? '연결' : '끊김' }}</span>
            <span class="badge" :class="room.door_id ? 'on' : 'off'">출입문 {{ room.door_id ? '연결' : '끊김' }}</span>
          </div>
        </div>
        <div class="seat-mini-grid">
          <div v-for="s in roomSeats(room.id)" :key="s.id" class="mini-seat" :class="s.status" :title="`${s.number}: ${s.status}`"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import apiClient from '@/services/api'

const stats = reactive({ totalUsers: 0, blacklistedUsers: 0, activeSeats: 0, qrIssuedToday: 0 })
const rooms = ref([])
const allSeats = ref({})

function roomSeats(roomId) { return allSeats.value[roomId] || [] }

onMounted(async () => {
  try {
    // Load rooms
    const { data: roomList } = await apiClient.get('/api/admin/rooms')
    rooms.value = roomList

    // Load seats per room
    let totalActive = 0
    for (const room of roomList) {
      const { data } = await apiClient.get(`/api/room/${room.code}/seats`)
      allSeats.value[room.id] = data.seats
      totalActive += data.seats.filter(s => s.status === 'occupied').length
    }
    stats.activeSeats = totalActive

    // Load user stats
    const { data: users } = await apiClient.get('/api/admin/users')
    stats.totalUsers = users.length
    stats.blacklistedUsers = users.filter(u => u.blacklist).length
  } catch (e) { console.error('Dashboard load error:', e) }
})
</script>

<style scoped>
.dashboard { max-width: 1000px; }
h1 { font-size: 24px; margin-bottom: 20px; }
h2 { font-size: 18px; margin-bottom: 12px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.stat-card { background: #fff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.stat-card.warn { border-left: 4px solid #e74c3c; }
.stat-card.ok { border-left: 4px solid #2ecc71; }
.stat-num { font-size: 32px; font-weight: bold; color: #333; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.section { margin-bottom: 24px; }
.room-card { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.room-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.room-header h3 { font-size: 16px; }
.badges { display: flex; gap: 8px; }
.badge { font-size: 12px; padding: 4px 8px; border-radius: 4px; }
.badge.on { background: #d4edda; color: #155724; }
.badge.off { background: #f8d7da; color: #721c24; }
.seat-mini-grid { display: flex; flex-wrap: wrap; gap: 4px; }
.mini-seat { width: 16px; height: 16px; border-radius: 3px; }
.mini-seat.empty { background: #bdc3c7; }
.mini-seat.occupied { background: #3498db; }
.mini-seat.disabled { background: #e74c3c; opacity: 0.5; }
</style>
