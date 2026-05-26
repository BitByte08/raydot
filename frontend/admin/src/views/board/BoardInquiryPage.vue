<template>
  <div class="page">
    <div class="top"><h1>문의사항 관리</h1></div>
    <div class="filters">
      <select v-model="status"><option value="">전체</option><option value="pending">대기</option><option value="answered">답변완료</option></select>
    </div>
    <table>
      <thead><tr><th>ID</th><th>내용</th><th>상태</th><th>답변</th><th>작업</th></tr></thead>
      <tbody>
        <tr v-for="i in inquiries" :key="i.id">
          <td>{{ i.id }}</td>
          <td class="content">{{ i.content.substring(0,50) }}{{ i.content.length > 50 ? '...' : '' }}</td>
          <td><span :class="i.status">{{ i.status === 'answered' ? '답변완료' : '대기' }}</span></td>
          <td>{{ i.reply ? i.reply.substring(0,30) + '...' : '-' }}</td>
          <td>
            <button v-if="i.status === 'pending'" @click="showReply(i)">답변</button>
            <button class="del" @click="deleteInquiry(i.id)">삭제</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="showReplyModal" class="modal">
      <div class="modal-box">
        <h2>답변 작성</h2>
        <div class="field"><label>문의 내용</label><p>{{ replying.content }}</p></div>
        <div class="field"><label>답변</label><textarea v-model="replyText" rows="4"></textarea></div>
        <div class="btns"><button @click="showReplyModal=false">취소</button><button class="primary" @click="submitReply">답변 등록</button></div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted, watch } from 'vue'; import apiClient from '@/services/api'
const inquiries = ref([]); const status = ref('')
const showReplyModal = ref(false); const replying = reactive({ id: null, content: '' })
const replyText = ref('')
async function load() { const params = {}; const { data } = await apiClient.get('/api/board/inquiry/0', { params }); inquiries.value = data.filter(i => status.value ? i.status === status.value : true) }
function showReply(i) { replying.id = i.id; replying.content = i.content; replyText.value = ''; showReplyModal.value = true }
async function submitReply() { await apiClient.post(`/api/admin/board/inquiry/${replying.id}/reply`, { reply: replyText.value }); showReplyModal.value = false; await load() }
async function deleteInquiry(id) { if (confirm('삭제하시겠습니까?')) { await apiClient.delete(`/api/admin/board/inquiry/${id}`); await load() } }
watch(status, load); onMounted(load)
</script>
<style scoped>
.page { max-width: 1000px; }
.top { margin-bottom: 16px; }
h1 { font-size: 24px; }
.filters { margin-bottom: 12px; }
.filters select { max-width: 150px; }
.content { max-width: 300px; }
.pending { color: #f39c12; font-weight: bold; }
.answered { color: #2ecc71; }
button { padding: 4px 8px; border-radius: 4px; font-size: 12px; background: #f0f0f5; }
.del { background: #e74c3c; color: #fff; margin-left: 4px; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
.modal-box { background: #fff; border-radius: 12px; padding: 24px; width: 500px; }
.modal-box h2 { font-size: 20px; margin-bottom: 16px; }
.field { margin-bottom: 12px; }
.field label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.field p { background: #f5f5f5; padding: 8px; border-radius: 4px; font-size: 14px; }
.btns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.primary { background: #4361ee; color: #fff; padding: 8px 16px; border-radius: 6px; }
</style>
