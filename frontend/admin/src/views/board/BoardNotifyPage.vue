<template>
  <div class="page">
    <div class="top"><h1>공지사항 관리</h1><button class="add-btn" @click="showForm = true">+ 등록</button></div>
    <table>
      <thead><tr><th>제목</th><th>작성자</th><th>등록일</th><th>작업</th></tr></thead>
      <tbody>
        <tr v-for="n in notices" :key="n.id">
          <td>{{ n.title }}</td><td>{{ n.author || '-' }}</td><td>{{ fmt(n.created_at) }}</td>
          <td><button @click="editNotice(n)">수정</button><button class="del" @click="deleteNotice(n.id)">삭제</button></td>
        </tr>
      </tbody>
    </table>
    <div v-if="showForm" class="modal">
      <div class="modal-box">
        <h2>{{ editing ? '공지 수정' : '공지 등록' }}</h2>
        <div class="field"><label>제목</label><input v-model="form.title" /></div>
        <div class="field"><label>내용 (마크다운)</label><textarea v-model="form.content" rows="6"></textarea></div>
        <div class="btns"><button @click="showForm=false">취소</button><button class="primary" @click="saveNotice">{{ editing ? '수정' : '등록' }}</button></div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted } from 'vue'; import apiClient from '@/services/api'
const notices = ref([]); const showForm = ref(false); const editing = ref(null)
const form = reactive({ title: '', content: '' })
function fmt(iso) { return iso ? new Date(iso).toLocaleDateString('ko-KR') : '' }
async function load() { const { data } = await apiClient.get('/api/board/notify'); notices.value = data }
function editNotice(n) { editing.value = n.id; form.title = n.title; form.content = n.content || ''; showForm.value = true }
async function saveNotice() {
  if (editing.value) { await apiClient.put(`/api/admin/board/notify/${editing.value}`, form) }
  else { await apiClient.post('/api/admin/board/notify', form) }
  showForm.value = false; editing.value = null; form.title = ''; form.content = ''; await load()
}
async function deleteNotice(id) { if (confirm('삭제하시겠습니까?')) { await apiClient.delete(`/api/admin/board/notify/${id}`); await load() } }
onMounted(load)
</script>
<style scoped>
.page { max-width: 1000px; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
h1 { font-size: 24px; }
.add-btn { padding: 8px 16px; background: #4361ee; color: #fff; border-radius: 6px; }
button { padding: 4px 8px; border-radius: 4px; font-size: 12px; background: #f0f0f5; }
.del { background: #e74c3c; color: #fff; margin-left: 4px; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
.modal-box { background: #fff; border-radius: 12px; padding: 24px; width: 500px; }
.modal-box h2 { font-size: 20px; margin-bottom: 16px; }
.field { margin-bottom: 12px; }
.field label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.field textarea { resize: vertical; }
.btns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.primary { background: #4361ee; color: #fff; padding: 8px 16px; border-radius: 6px; }
</style>
