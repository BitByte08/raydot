<template>
  <div class="screen">
    <div class="head"><button @click="$router.back()">←</button><h2>입실</h2></div>
    <div class="body">
      <div class="seat-info">좌석 {{ seatNum }}</div>
      <div class="pass-options">
        <label v-for="p in passes" :key="p.value" class="pass-option" :class="{ sel: passType === p.value }">
          <input type="radio" :value="p.value" v-model="passType" />
          <span>{{ p.label }}</span>
        </label>
      </div>
      <button class="confirm" @click="doCheckIn" :disabled="loading">
        {{ loading ? '처리 중...' : '입실하기' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRoomStore } from '@/stores/room'
import apiClient from '@/services/api'

const route = useRoute(); const router = useRouter()
const authStore = useAuthStore(); const roomStore = useRoomStore()
const seatId = ref(route.query.sid); const seatNum = ref(route.query.snum)
const passType = ref('daily'); const loading = ref(false)
const passes = [
  { value: 'daily', label: '당일권' },
  { value: 'weekly', label: '정기권 (주간)' },
  { value: 'monthly', label: '정기권 (월간)' },
]

async function doCheckIn() {
  loading.value = true
  try {
    const code = roomStore.roomCode
    if (!code) { alert('정독실 정보를 불러올 수 없습니다.'); return }
    const { data } = await apiClient.post(`/api/room/${code}/check-in`, {
      seat_id: Number(seatId.value),
      user_id: authStore.user?.id,
      pass_type: passType.value,
    })
    if (data.success) {
      router.push({ name: 'qr', query: { qr: data.qr_code, exp: data.expires_at } })
    }
  } catch (e) {
    alert(e.response?.data?.detail || '입실 실패')
  } finally { loading.value = false }
}
</script>

<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.body { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; }
.seat-info { font-size: 28px; font-weight: bold; margin-bottom: 24px; }
.pass-options { display: flex; flex-direction: column; gap: 12px; width: 300px; margin-bottom: 24px; }
.pass-option { display: flex; align-items: center; gap: 12px; padding: 14px 16px; background: #fff; border-radius: 8px; border: 2px solid #ddd; cursor: pointer; min-height: 52px; font-size: 16px; }
.pass-option.sel { border-color: #4361ee; background: #eef0ff; }
.confirm { width: 300px; padding: 14px; background: #4361ee; color: #fff; border-radius: 12px; font-size: 18px; }
.confirm:disabled { background: #ccc; }
</style>
