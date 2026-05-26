<template>
  <div class="page" v-if="user">
    <div class="top"><h1>{{ user.name }}</h1><router-link to="/users">← 목록</router-link></div>
    <div class="info-card">
      <div class="row"><span>학번</span><span>{{ user.student_id }}</span></div>
      <div class="row"><span>이메일</span><span>{{ user.email }}</span></div>
      <div class="row"><span>이용 제한</span><span :class="user.blacklist ? 'bl' : ''">{{ user.blacklist ? '제한 중' : '정상' }}</span></div>
    </div>
    <div class="section">
      <h2>블랙리스트 관리</h2>
      <div v-if="!user.blacklist" class="bl-form">
        <select v-model="blDuration"><option value="1w">1주일</option><option value="1m">1개월</option><option value="permanent">영구</option></select>
        <input v-model="blReason" placeholder="사유 입력" />
        <button class="danger" @click="addBL">등록</button>
      </div>
      <div v-else>
        <p>사유: {{ user.blacklist_reason || '없음' }}</p>
        <button class="primary" @click="removeBL">해제</button>
      </div>
    </div>
    <div class="section">
      <h2>이용 기록</h2>
      <table>
        <thead><tr><th>날짜</th><th>입실</th><th>퇴실</th><th>좌석</th></tr></thead>
        <tbody><tr v-for="l in logs" :key="l.date + l.check_in_time"><td>{{ l.date }}</td><td>{{ fmt(l.check_in_time) }}</td><td>{{ fmt(l.check_out_time) || '-' }}</td><td>{{ l.seat_number }}</td></tr></tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'; import { useRoute } from 'vue-router'; import apiClient from '@/services/api'
const route = useRoute(); const sid = route.params.id
const user = ref(null); const logs = ref([])
const blDuration = ref('1w'); const blReason = ref('')
function fmt(iso) { return iso ? new Date(iso).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '' }
async function load() {
  const { data: u } = await apiClient.get(`/api/user/${sid}`); user.value = u
  const { data: l } = await apiClient.get(`/api/admin/user/${sid}/logs`); logs.value = l
}
async function addBL() {
  await apiClient.post(`/api/admin/user/${sid}/blacklist`, { duration: blDuration.value, reason: blReason.value }); await load()
}
async function removeBL() {
  await apiClient.delete(`/api/admin/user/${sid}/blacklist`); await load()
}
onMounted(load)
</script>
<style scoped>
.page { max-width: 800px; }
h1 { font-size: 24px; }
h2 { font-size: 18px; margin: 16px 0 8px; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.top a { color: #4361ee; text-decoration: none; }
.info-card { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
.row span:first-child { color: #999; }
.bl { color: #e74c3c; font-weight: bold; }
.section { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.bl-form { display: flex; gap: 8px; margin-top: 8px; }
.bl-form select, .bl-form input { max-width: 200px; }
.danger { background: #e74c3c; color: #fff; padding: 8px 16px; border-radius: 6px; }
.primary { background: #4361ee; color: #fff; padding: 8px 16px; border-radius: 6px; }
</style>
