<template>
  <div class="screen">
    <div class="head"><button @click="$router.back()">←</button><h2>비밀번호 변경</h2></div>
    <div class="body">
      <PinKeypad title="현재 PIN 입력" v-if="step === 1" @confirm="s1" @cancel="$router.back()" />
      <PinKeypad title="새 PIN 입력" v-if="step === 2" @confirm="s2" @cancel="step=1" />
      <PinKeypad title="새 PIN 확인" v-if="step === 3" @confirm="s3" @cancel="step=2" />
      <div v-if="done" class="done-box">
        <h3>✓ 변경 완료</h3>
        <button @click="$router.push('/desk')">확인</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/services/api'
import PinKeypad from '@/components/PinKeypad.vue'

const authStore = useAuthStore()
const step = ref(1)
const currentPin = ref('')
const newPin = ref('')
const done = ref(false)

function s1(pin) { currentPin.value = pin; step.value = 2 }
function s2(pin) { newPin.value = pin; step.value = 3 }
async function s3(pin) {
  if (pin !== newPin.value) { alert('PIN이 일치하지 않습니다'); step.value = 2; return }
  try {
    await apiClient.post(`/api/user/${authStore.user?.student_id}/password/reset`, { current_pin: currentPin.value, new_pin: newPin.value })
    done.value = true
  } catch (e) { alert(e.response?.data?.detail || '변경 실패'); step.value = 1 }
}
</script>
<style scoped>
.screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.head { display: flex; align-items: center; padding: 8px 12px; background: #1a1a2e; color: #fff; }
.head button { background: none; color: #fff; font-size: 20px; min-width: 44px; }
.head h2 { flex: 1; text-align: center; font-size: 20px; }
.body { flex: 1; display: flex; align-items: center; justify-content: center; }
.done-box { text-align: center; }
.done-box h3 { font-size: 24px; color: #2ecc71; margin-bottom: 16px; }
.done-box button { padding: 12px 32px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 16px; }
</style>
