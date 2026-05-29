<template>
  <div class="page">
    <div class="top">
      <h1>관리자 관리</h1>
      <div class="top-actions">
        <router-link to="/admins/pin" class="pin-btn">내 PIN 설정</router-link>
        <router-link to="/admins/create" class="add-btn">+ 관리자 추가</router-link>
      </div>
    </div>
    <table>
      <thead><tr><th>이메일</th><th>이름</th><th>역할</th><th>이메일 인증</th><th>키오스크 PIN</th><th></th></tr></thead>
      <tbody>
        <tr v-for="a in admins" :key="a.id">
          <td>{{ a.email }}</td>
          <td>{{ a.name }}</td>
          <td><span class="role" :class="a.role">{{ a.role }}</span></td>
          <td>{{ a.verified ? '✓' : '✗' }}</td>
          <td>{{ a.has_pin ? '설정됨' : '없음' }}</td>
          <td><button class="del" @click="remove(a)">삭제</button></td>
        </tr>
      </tbody>
    </table>
    <p v-if="admins.length === 0" class="empty">관리자가 없습니다</p>
    <p v-if="msg" class="err">{{ msg }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/services/api'

const admins = ref([])
const msg = ref('')

async function load() {
  try { const { data } = await apiClient.get('/api/admin/admins'); admins.value = data }
  catch (e) { msg.value = e.response?.data?.detail || '목록 불러오기 실패' }
}

async function remove(a) {
  if (!confirm(`${a.email} 관리자를 삭제하시겠습니까?`)) return
  msg.value = ''
  try { await apiClient.delete(`/api/admin/admins/${a.id}`); await load() }
  catch (e) { msg.value = e.response?.data?.detail || '삭제 실패' }
}

onMounted(load)
</script>

<style scoped>
.page { max-width: 1000px; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.top-actions { display: flex; gap: 8px; }
h1 { font-size: 24px; }
.add-btn { padding: 8px 16px; background: #4361ee; color: #fff; border-radius: 6px; text-decoration: none; font-size: 14px; }
.pin-btn { padding: 8px 16px; background: #f0f0f5; color: #333; border-radius: 6px; text-decoration: none; font-size: 14px; }
table { width: 100%; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { text-align: left; padding: 12px 16px; border-bottom: 1px solid #eee; }
th { background: #fafafa; font-size: 13px; color: #666; }
.role { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.role.superadmin { background: #e74c3c; color: #fff; }
.role.manager { background: #f39c12; color: #fff; }
.role.staff { background: #eee; color: #666; }
.del { padding: 4px 12px; background: #e74c3c; color: #fff; border-radius: 4px; font-size: 13px; }
.empty { text-align: center; color: #999; padding: 40px; }
.err { color: #e74c3c; margin-top: 12px; }
</style>
