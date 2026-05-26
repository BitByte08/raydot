<template>
  <div class="screen">
    <div class="head"><h2>최초 비밀번호 설정</h2></div>
    <div class="body">
      <p>안전한 이용을 위해 4자리 PIN을 설정해주세요.</p>
      <p class="id">학번: {{ studentId }}</p>
    </div>
    <PinKeypad title="PIN 설정" @confirm="submit" @cancel="$router.push('/login')" />
  </div>
</template>
<script setup>
import { ref } from 'vue'; import { useRouter } from 'vue-router'; import apiClient from '@/services/api'; import PinKeypad from '@/components/PinKeypad.vue'
const router = useRouter(); const studentId = ref(router.currentRoute.value.query.sid || '')
async function submit(pin) {
  try { await apiClient.post('/api/auth/password/initial', { student_id: studentId.value, pin }); router.push('/login') }
  catch(e) { alert('설정 실패') }
}
</script>
<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; }
.head { padding: 16px; background: #1a1a2e; color: #fff; text-align: center; }
.head h2 { font-size: 20px; }
.body { padding: 32px 24px; text-align: center; font-size: 16px; }
.id { margin-top: 12px; color: #4361ee; font-weight: bold; }
</style>
