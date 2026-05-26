<template>
  <div class="splash" @click="goLogin">
    <div class="logo-area">
      <div class="logo-icon">📚</div>
      <h1>Raydot</h1>
      <p class="subtitle">정독실 출입 관리 시스템</p>
    </div>
    <p class="hint">화면을 터치하세요</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

function goLogin() {
  router.push('/login')
}

onMounted(() => {
  setTimeout(() => router.push('/login'), 3000)
})
</script>

<style scoped>
.splash {
  width: 800px;
  height: 480px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  cursor: pointer;
}
.logo-area {
  text-align: center;
}
.logo-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
h1 {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 8px;
}
.subtitle {
  font-size: 16px;
  opacity: 0.7;
}
.hint {
  position: absolute;
  bottom: 24px;
  font-size: 14px;
  opacity: 0.5;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}
</style>
