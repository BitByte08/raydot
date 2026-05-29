<template>
  <StudentGate title="내 정보">
    <template #default="{ user }">
      <div class="body">
        <div class="info-row"><span class="label">학번</span><span class="val">{{ user.student_id }}</span></div>
        <div class="info-row"><span class="label">이름</span><span class="val">{{ user.name }}</span></div>
        <div class="info-row"><span class="label">이메일</span><span class="val">{{ user.email }}</span></div>
        <div class="info-row">
          <span class="label">상태</span>
          <span class="val" :class="{ bl: user.blacklist }">{{ user.blacklist ? '이용 제한' : '정상' }}</span>
        </div>
      </div>
      <div class="actions">
        <button @click="$router.push('/user/log')">이용 기록</button>
        <button @click="$router.push('/user/password/reset')">비밀번호 변경</button>
        <button @click="$router.push('/')">뒤로</button>
      </div>
    </template>
  </StudentGate>
</template>

<script setup>
import StudentGate from '@/components/StudentGate.vue'
</script>

<style scoped>
.body { flex: 1; padding: 16px; }
.info-row { display: flex; justify-content: space-between; padding: 14px 16px; background: #fff; margin-bottom: 8px; border-radius: 8px; font-size: 16px; }
.label { color: #999; }
.val { font-weight: bold; }
.val.bl { color: #e74c3c; }
.actions { display: flex; gap: 8px; padding: 12px 16px; }
.actions button { flex: 1; padding: 12px; border-radius: 8px; font-size: 14px; background: #fff; }
.actions button:first-child { background: #4361ee; color: #fff; }
</style>
