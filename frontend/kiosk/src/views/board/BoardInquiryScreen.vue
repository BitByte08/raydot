<template>
  <div class="screen">
    <div class="head"><button @click="$router.push('/desk')">←</button><h2>문의사항</h2></div>
    <div class="list">
      <div v-for="i in inquiries" :key="i.id" class="item">
        <div class="row"><span class="status" :class="i.status">{{ i.status === 'answered' ? '답변완료' : '대기' }}</span><span class="content">{{ i.content }}</span></div>
        <div v-if="i.reply" class="reply"><strong>답변:</strong> {{ i.reply }}</div>
      </div>
      <p v-if="inquiries.length === 0" class="empty">문의사항이 없습니다</p>
    </div>
    <div class="bottom">
      <button class="write-btn" @click="$router.push('/board/inquiry/new')">문의 등록</button>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/services/api'
const authStore = useAuthStore()
const inquiries = ref([])
onMounted(async () => {
  try {
    const { data } = await apiClient.get(`/api/board/inquiry/${authStore.user?.id}`)
    inquiries.value = data
  } catch (e) {}
})
</script>
<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.list { flex: 1; padding: 8px 12px; overflow-y: auto; }
.item { background: #fff; border-radius: 8px; margin-bottom: 6px; padding: 12px 16px; }
.row { display: flex; gap: 8px; align-items: center; }
.status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.status.pending { background: #fff3cd; color: #856404; }
.status.answered { background: #d4edda; color: #155724; }
.content { font-size: 14px; }
.reply { margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; font-size: 14px; color: #4361ee; }
.empty { text-align: center; color: #999; padding: 40px; }
.bottom { padding: 8px 12px; }
.write-btn { width: 100%; padding: 12px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 16px; }
</style>
