<template>
  <StudentGate title="이용 기록" @verified="onVerified">
    <template #default="{ user, token }">
      <div class="filters">
        <button v-for="f in filters" :key="f.v" :class="{ active: range === f.v }"
          @click="loadLogs(user, token, f.v)">{{ f.l }}</button>
      </div>
      <div class="list">
        <div v-for="log in logs" :key="log.date + log.check_in_time" class="log-row">
          <span class="date">{{ log.date }}</span>
          <span class="time">{{ fmtTime(log.check_in_time) }} ~ {{ fmtTime(log.check_out_time) || '이용 중' }}</span>
          <span class="seat">{{ log.seat_number }}</span>
        </div>
        <p v-if="!logsLoading && logs.length === 0" class="empty">기록이 없습니다</p>
      </div>
    </template>
  </StudentGate>
</template>

<script setup>
import { ref } from 'vue'
import apiClient from '@/services/api'
import StudentGate from '@/components/StudentGate.vue'

const logs = ref([])
const logsLoading = ref(false)
const range = ref('30d')
const filters = [{ v: '7d', l: '7일' }, { v: '14d', l: '14일' }, { v: '30d', l: '30일' }]

function fmtTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

async function loadLogs(user, token, r) {
  range.value = r
  logsLoading.value = true
  try {
    const { data } = await apiClient.get(`/api/user/${user.student_id}/logs`, {
      params: { range: r },
      headers: { Authorization: `Bearer ${token}` },
    })
    logs.value = data
  } catch (e) { console.error('logs load failed', e) }
  finally { logsLoading.value = false }
}

function onVerified(user, token) { loadLogs(user, token, '30d') }
</script>

<style scoped>
.filters { display: flex; gap: 8px; padding: 8px 12px; }
.filters button { padding: 8px 16px; border-radius: 20px; font-size: 14px; background: #fff; }
.filters button.active { background: #4361ee; color: #fff; }
.list { flex: 1; padding: 0 12px; overflow-y: auto; }
.log-row { display: flex; align-items: center; padding: 12px 16px; background: #fff; margin-bottom: 6px; border-radius: 8px; font-size: 14px; }
.date { width: 90px; font-weight: bold; }
.time { flex: 1; color: #666; }
.seat { width: 60px; text-align: right; color: #4361ee; font-weight: bold; }
.empty { text-align: center; color: #999; padding: 40px; }
</style>
