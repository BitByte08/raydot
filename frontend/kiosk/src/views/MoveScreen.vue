<template>
  <div class="screen">
    <div class="head"><button @click="$router.back()">←</button><h2>좌석 이동</h2></div>
    <div class="body">
      <p>이동할 좌석을 선택하세요</p>
      <div class="grid">
        <div v-for="s in availableSeats" :key="s.id" class="seat" :class="{ sel: selectedId === s.id }" @click="selectedId = s.id">
          {{ s.number }}
        </div>
        <p v-if="availableSeats.length === 0" class="empty">이동 가능한 좌석이 없습니다</p>
      </div>
      <button class="confirm" :disabled="!selectedId || loading" @click="doMove">
        {{ loading ? '처리 중...' : '이동하기' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRoomStore } from '@/stores/room'
import apiClient from '@/services/api'

const route = useRoute(); const router = useRouter()
const authStore = useAuthStore(); const roomStore = useRoomStore()
const fromSeatId = ref(route.query.sid)
const selectedId = ref(null)
const availableSeats = ref([])
const loading = ref(false)

onMounted(async () => {
  const code = roomStore.roomCode
  if (!code) return
  try {
    const { data } = await apiClient.get(`/api/room/${code}/seats`)
    availableSeats.value = data.seats.filter(
      s => s.status === 'empty' && s.id !== Number(fromSeatId.value)
    )
  } catch (e) { console.error('Failed to load seats:', e) }
})

async function doMove() {
  loading.value = true
  try {
    const code = roomStore.roomCode
    await apiClient.post(`/api/room/${code}/seat/move`, {
      from_seat_id: Number(fromSeatId.value),
      to_seat_id: selectedId.value,
      user_id: authStore.user?.id,
    })
    router.push('/desk')
  } catch (e) { alert(e.response?.data?.detail || '이동 실패') }
  finally { loading.value = false }
}
</script>

<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.body { flex: 1; padding: 16px; text-align: center; }
.body > p { font-size: 16px; margin-bottom: 12px; }
.grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 16px; }
.seat { padding: 16px; background: #bdc3c7; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; }
.seat:active { transform: scale(0.95); }
.seat.sel { background: #2ecc71; color: #fff; }
.empty { grid-column: 1/-1; color: #999; padding: 24px; }
.confirm { width: 300px; padding: 14px; background: #4361ee; color: #fff; border-radius: 12px; font-size: 18px; }
.confirm:disabled { background: #ccc; }
</style>
