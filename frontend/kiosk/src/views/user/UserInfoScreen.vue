<template>
  <div class="screen">
    <div class="head"><button @click="$router.push('/desk')">←</button><h2>내 정보</h2></div>
    <div class="body" v-if="user">
      <div class="info-row"><span class="label">학번</span><span class="val">{{ user.student_id }}</span></div>
      <div class="info-row"><span class="label">이름</span><span class="val">{{ user.name }}</span></div>
      <div class="info-row"><span class="label">이메일</span><span class="val">{{ user.email }}</span></div>
      <div class="info-row"><span class="label">상태</span><span class="val" :class="{ bl: user.blacklist }">{{ user.blacklist ? '이용 제한' : '정상' }}</span></div>
    </div>
    <div class="actions">
      <button @click="$router.push('/user/log')">이용 기록</button>
      <button @click="$router.push('/user/password/reset')">비밀번호 변경</button>
      <button @click="$router.push('/desk')">뒤로</button>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
const user = ref(authStore.user)
</script>
<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.body { flex: 1; padding: 16px; }
.info-row { display: flex; justify-content: space-between; padding: 14px 16px; background: #fff; margin-bottom: 8px; border-radius: 8px; font-size: 16px; }
.label { color: #999; }
.val { font-weight: bold; }
.val.bl { color: #e74c3c; }
.actions { display: flex; gap: 8px; padding: 12px 16px; }
.actions button { flex: 1; padding: 12px; border-radius: 8px; font-size: 14px; background: #fff; }
.actions button:first-child { background: #4361ee; color: #fff; }
</style>
