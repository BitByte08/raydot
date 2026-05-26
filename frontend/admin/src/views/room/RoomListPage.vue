<template>
  <div class="page">
    <div class="top"><h1>정독실 관리</h1></div>
    <div class="room-grid">
      <div v-for="r in rooms" :key="r.id" class="room-card" @click="$router.push(`/rooms/${r.code}`)">
        <h3>{{ r.name }}</h3>
        <p class="code">{{ r.code }}</p>
        <div class="status-row">
          <span class="badge" :class="r.kiosk_id ? 'on' : 'off'">키오스크 {{ r.kiosk_id ? '연결' : '미연결' }}</span>
          <span class="badge" :class="r.door_id ? 'on' : 'off'">출입문 {{ r.door_id ? '연결' : '미연결' }}</span>
        </div>
      </div>
    </div>
    <button class="add-btn" @click="showCreate = true">+ 정독실 추가</button>
    <div v-if="showCreate" class="modal">
      <div class="modal-box">
        <h2>정독실 생성</h2>
        <div class="field"><label>코드</label><input v-model="newRoom.code" placeholder="R001" /></div>
        <div class="field"><label>이름</label><input v-model="newRoom.name" placeholder="제1정독실" /></div>
        <div class="field"><label>좌석 수</label><input v-model.number="newRoom.seatCount" type="number" min="1" max="50" /></div>
        <div class="btns"><button @click="showCreate=false">취소</button><button class="primary" @click="createRoom">생성</button></div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'; import apiClient from '@/services/api'
const rooms = ref([]); const showCreate = ref(false)
const newRoom = reactive({ code: '', name: '', seatCount: 20 })
onMounted(async () => { try { const { data } = await apiClient.get('/api/admin/rooms'); rooms.value = data } catch(e) {} })
async function createRoom() {
  const seats = []; for (let i = 1; i <= newRoom.seatCount; i++) seats.push({ number: `A${String(i).padStart(2,'0')}`, enabled: true })
  try { await apiClient.post('/api/admin/room/create', { code: newRoom.code, name: newRoom.name, seats }); showCreate.value = false; onMounted() }
  catch(e) { alert(e.response?.data?.detail || '생성 실패') }
}
</script>
<style scoped>
.page { max-width: 1000px; }
.top { margin-bottom: 16px; }
h1 { font-size: 24px; }
.room-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.room-card { background: #fff; border-radius: 8px; padding: 16px; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.room-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.room-card h3 { font-size: 18px; margin-bottom: 4px; }
.code { font-size: 13px; color: #999; margin-bottom: 8px; }
.status-row { display: flex; gap: 8px; }
.badge { font-size: 12px; padding: 4px 8px; border-radius: 4px; }
.badge.on { background: #d4edda; color: #155724; }
.badge.off { background: #f8d7da; color: #721c24; }
.add-btn { padding: 10px 20px; background: #4361ee; color: #fff; border-radius: 6px; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
.modal-box { background: #fff; border-radius: 12px; padding: 24px; width: 400px; }
.modal-box h2 { font-size: 20px; margin-bottom: 16px; }
.field { margin-bottom: 12px; }
.field label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.btns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.primary { background: #4361ee; color: #fff; padding: 8px 16px; border-radius: 6px; }
</style>
