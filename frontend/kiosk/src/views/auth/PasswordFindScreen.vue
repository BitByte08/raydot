<template>
  <div class="screen">
    <div class="head"><h2>비밀번호 찾기</h2></div>
    <div class="body">
      <div v-if="!sent">
        <div class="scan-icon">💳</div>
        <p>학생증을 스캔해주세요</p>
        <input v-model="sid" type="text" placeholder="또는 학번 직접 입력" @keyup.enter="send" />
        <button @click="send" :disabled="!sid">재설정 링크 발송</button>
      </div>
      <div v-else class="done">
        <h3>이메일 발송 완료</h3>
        <p>등록된 이메일로 재설정 링크가 발송되었습니다.</p>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'; import apiClient from '@/services/api'
const sid = ref(''); const sent = ref(false)
async function send() {
  if (!sid.value) return
  try { await apiClient.post('/api/auth/password/find', { student_id: sid.value }); sent.value = true }
  catch(e) { alert('발송 실패') }
}
</script>
<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; }
.head { padding: 16px; background: #1a1a2e; color: #fff; text-align: center; }
.head h2 { font-size: 20px; }
.body { padding: 32px 24px; text-align: center; }
.scan-icon { font-size: 64px; margin-bottom: 12px; }
.body p { font-size: 16px; color: #666; margin-bottom: 16px; }
.body input { width: 260px; text-align: center; font-size: 16px; margin-bottom: 12px; }
.body button { width: 260px; padding: 14px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 16px; }
.body button:disabled { background: #ccc; }
.done h3 { color: #2ecc71; font-size: 20px; margin-bottom: 8px; }
</style>
