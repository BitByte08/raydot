<template>
  <div class="page">
    <div class="top"><h1>QR 관리</h1></div>
    <div class="filters">
      <select v-model="status"><option value="">전체</option><option value="unused">미사용</option><option value="used">사용됨</option></select>
    </div>
    <table>
      <thead><tr><th>ID</th><th>생성일</th><th>사용자</th><th>좌석</th><th>상태</th><th>만료</th><th>작업</th></tr></thead>
      <tbody>
        <tr v-for="q in qrs" :key="q.id">
          <td>{{ q.id }}</td>
          <td>{{ fmt(q.created_at) }}</td>
          <td>{{ q.user_id }}</td>
          <td>{{ q.seat_id }}</td>
          <td><span :class="q.used ? 'used' : 'unused'">{{ q.used ? '사용됨' : '미사용' }}</span></td>
          <td>{{ fmt(q.expires_at) }}</td>
          <td><button v-if="!q.used" class="revoke" @click="revoke(q.id)">폐기</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup>
import { ref, onMounted, watch } from 'vue'; import apiClient from '@/services/api'
const qrs = ref([]); const status = ref('')
function fmt(iso) { return iso ? new Date(iso).toLocaleString('ko-KR') : '-' }
async function load() {
  const params = status.value ? { status: status.value } : {}
  const { data } = await apiClient.get('/api/admin/qr', { params }); qrs.value = data
}
async function revoke(id) { await apiClient.post(`/api/admin/qr/revoke/${id}`); await load() }
watch(status, load); onMounted(load)
</script>
<style scoped>
.page { max-width: 1000px; }
.top { margin-bottom: 16px; }
h1 { font-size: 24px; }
.filters { margin-bottom: 12px; }
.filters select { max-width: 150px; }
.used { color: #999; }
.unused { color: #2ecc71; font-weight: bold; }
.revoke { padding: 4px 8px; background: #e74c3c; color: #fff; border-radius: 4px; font-size: 12px; }
</style>
