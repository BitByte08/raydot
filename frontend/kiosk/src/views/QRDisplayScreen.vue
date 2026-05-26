<template>
  <div class="screen">
    <div class="head"><h2>QR 코드</h2></div>
    <div class="body">
      <canvas ref="qrCanvas" class="qr-canvas"></canvas>
      <p class="guide">정독실 입장 시 QR을 스캔하세요</p>
      <p class="expire" v-if="expiresAt">유효시간: {{ remaining }}초</p>
      <button class="ok-btn" @click="$router.push('/desk')">확인</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'

const route = useRoute()
const router = useRouter()
const qrCanvas = ref(null)
const qrString = ref(route.query.qr || '')
const expiresAt = ref(route.query.exp ? new Date(route.query.exp) : null)
const remaining = ref(1800)

let timer = null

onMounted(async () => {
  if (!qrString.value) { router.push('/desk'); return }

  // Generate real QR code image on canvas
  try {
    await QRCode.toCanvas(qrCanvas.value, qrString.value, {
      width: 200,
      margin: 2,
      color: { dark: '#000000', light: '#ffffff' },
    })
  } catch (e) {
    console.error('QR generation failed:', e)
  }

  // Countdown timer
  if (expiresAt.value) {
    timer = setInterval(() => {
      const diff = Math.max(0, Math.floor((expiresAt.value - new Date()) / 1000))
      remaining.value = diff
      if (diff <= 0) { clearInterval(timer); router.push('/desk') }
    }, 1000)
  }
})

onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.screen { width: 800px; height: 480px; background: #fff; display: flex; flex-direction: column; }
.head { padding: 12px; background: #1a1a2e; color: #fff; text-align: center; }
.head h2 { font-size: 20px; }
.body { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; }
.qr-canvas { margin-bottom: 16px; }
.guide { font-size: 16px; color: #333; margin-bottom: 8px; }
.expire { font-size: 14px; color: #e74c3c; margin-bottom: 20px; font-weight: bold; }
.ok-btn { padding: 12px 48px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 16px; }
</style>
