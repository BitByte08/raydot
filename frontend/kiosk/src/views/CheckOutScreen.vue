<template>
  <div class="screen">
    <div class="head"><button @click="$router.back()">←</button><h2>퇴실</h2></div>
    <div class="body">
      <div class="seat-info">좌석 {{ seatNum }}</div>
      <p>{{ seatNum }} 좌석에서 퇴실하시겠습니까?</p>
      <div class="btns">
        <button class="cancel" @click="$router.back()">취소</button>
        <button class="confirm" @click="doCheckOut" :disabled="loading">
          {{ loading ? '처리 중...' : '퇴실하기' }}
        </button>
      </div>
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
const loading = ref(false)

async function doCheckOut() {
  loading.value = true
  try {
    const code = roomStore.roomCode
    if (!code) { alert('정독실 정보를 불러올 수 없습니다.'); return }
    await apiClient.post(`/api/room/${code}/check-out`, {
      seat_id: Number(seatId.value),
      user_id: authStore.user?.id,
    })
    router.push('/desk')
  } catch (e) { alert(e.response?.data?.detail || '퇴실 실패') }
  finally { loading.value = false }
}
</script>

<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.body { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; }
.seat-info { font-size: 36px; font-weight: bold; margin-bottom: 12px; }
.body p { font-size: 18px; color: #666; margin-bottom: 24px; }
.btns { display: flex; gap: 12px; }
.btns button { padding: 14px 32px; border-radius: 12px; font-size: 18px; min-width: 140px; }
.cancel { background: #f0f0f5; color: #666; }
.confirm { background: #e74c3c; color: #fff; }
.confirm:disabled { background: #ccc; }
</style>
