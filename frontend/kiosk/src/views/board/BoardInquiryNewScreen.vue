<template>
  <div class="screen">
    <div class="head"><button @click="$router.back()">←</button><h2>문의 등록</h2></div>
    <div class="body">
      <textarea v-model="content" placeholder="문의 내용을 입력하세요" rows="6" maxlength="500"></textarea>
      <span class="count">{{ content.length }}/500</span>
      <button class="submit" :disabled="!content.trim() || loading" @click="submit">
        {{ loading ? '등록 중...' : '등록하기' }}
      </button>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/services/api'
const router = useRouter(); const authStore = useAuthStore()
const content = ref(''); const loading = ref(false)
async function submit() {
  loading.value = true
  try {
    await apiClient.post('/api/board/inquiry', { user_id: authStore.user?.id, content: content.value })
    router.push('/board/inquiry')
  } catch (e) { alert('등록 실패') }
  finally { loading.value = false }
}
</script>
<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.body { flex: 1; padding: 16px; display: flex; flex-direction: column; }
textarea { width: 100%; flex: 1; resize: none; font-size: 16px; padding: 12px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 4px; }
.count { font-size: 12px; color: #999; text-align: right; margin-bottom: 8px; }
.submit { padding: 14px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 18px; }
.submit:disabled { background: #ccc; }
</style>
