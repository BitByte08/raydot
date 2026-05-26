<template>
  <div class="page">
    <div class="top">
      <h1>사용자 관리</h1>
      <router-link to="/users/create" class="add-btn">+ 사용자 추가</router-link>
    </div>
    <div class="filters">
      <input v-model="search" type="text" placeholder="학번 또는 이름 검색" />
    </div>
    <table>
      <thead><tr><th>학번</th><th>이름</th><th>이메일</th><th>이용 제한</th><th>PIN 설정</th></tr></thead>
      <tbody>
        <tr v-for="u in filtered" :key="u.id" @click="$router.push(`/users/${u.student_id}`)" style="cursor:pointer">
          <td>{{ u.student_id }}</td><td>{{ u.name }}</td><td>{{ u.email }}</td>
          <td><span :class="u.blacklist ? 'bl' : 'ok'">{{ u.blacklist ? '제한' : '정상' }}</span></td>
          <td>{{ u.password_set ? '✓' : '✗' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="filtered.length === 0" class="empty">사용자가 없습니다</p>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'; import apiClient from '@/services/api'
const users = ref([]); const search = ref('')
const filtered = computed(() => {
  if (!search.value) return users.value
  const q = search.value.toLowerCase()
  return users.value.filter(u => u.student_id.includes(q) || u.name.toLowerCase().includes(q))
})
onMounted(async () => { try { const { data } = await apiClient.get('/api/admin/users'); users.value = data } catch(e) {} })
</script>
<style scoped>
.page { max-width: 1000px; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
h1 { font-size: 24px; }
.add-btn { padding: 8px 16px; background: #4361ee; color: #fff; border-radius: 6px; text-decoration: none; font-size: 14px; }
.filters { margin-bottom: 12px; }
.filters input { max-width: 300px; }
.bl { color: #e74c3c; font-weight: bold; }
.ok { color: #2ecc71; }
.empty { text-align: center; color: #999; padding: 40px; }
</style>
