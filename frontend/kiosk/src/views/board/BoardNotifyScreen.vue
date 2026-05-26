<template>
  <div class="screen">
    <div class="head"><button @click="$router.push('/desk')">←</button><h2>공지사항</h2></div>
    <div class="list">
      <div v-for="n in notices" :key="n.id" class="item" @click="selected = selected?.id === n.id ? null : n">
        <div class="title-row">
          <span class="title">{{ n.title }}</span>
          <span class="date">{{ fmtDate(n.created_at) }}</span>
        </div>
        <div v-if="selected?.id === n.id" class="content" v-html="n.content"></div>
      </div>
      <p v-if="notices.length === 0" class="empty">공지사항이 없습니다</p>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoomStore } from '@/stores/room'
import apiClient from '@/services/api'
const roomStore = useRoomStore()
const notices = ref([])
const selected = ref(null)
function fmtDate(iso) { if (!iso) return ''; return new Date(iso).toLocaleDateString('ko-KR') }
onMounted(async () => {
  try {
    const code = roomStore.roomCode
    const { data } = await apiClient.get('/api/board/notify', { params: { room_code: code } })
    notices.value = data
  } catch (e) {}
})
</script>
<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.list { flex: 1; padding: 8px 12px; overflow-y: auto; }
.item { background: #fff; border-radius: 8px; margin-bottom: 6px; padding: 12px 16px; cursor: pointer; }
.title-row { display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 16px; font-weight: bold; }
.date { font-size: 12px; color: #999; }
.content { margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; font-size: 14px; line-height: 1.6; color: #555; }
.empty { text-align: center; color: #999; padding: 40px; }
</style>
