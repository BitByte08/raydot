<template>
  <div class="pin-overlay" @click.self="$emit('cancel')">
    <div class="pin-box">
      <h3>{{ title }}</h3>
      <div class="dots">
        <span v-for="i in 4" :key="i" :class="{ on: i <= p.length }">●</span>
      </div>
      <div class="grid">
        <button v-for="n in 9" :key="n" @click="press(n)">{{ n }}</button>
        <b class="ghost"></b>
        <button @click="press(0)">0</button>
        <button class="del" @click="pop">←</button>
      </div>
      <div class="btns">
        <b class="cancel" @click="$emit('cancel')">취소</b>
        <b class="ok" :class="{ off: p.length < 4 }" @click="ok">확인</b>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ title: { type: String, default: 'PIN 입력' } })
const emit = defineEmits(['confirm', 'cancel'])
const p = ref('')
function press(n) { if (p.value.length < 4) p.value += n }
function pop() { p.value = p.value.slice(0, -1) }
function ok() { if (p.value.length === 4) emit('confirm', p.value) }
</script>

<style scoped>
.pin-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.pin-box { background: #fff; border-radius: 16px; padding: 24px; width: 340px; text-align: center; }
h3 { font-size: 20px; margin-bottom: 16px; }
.dots { display: flex; justify-content: center; gap: 16px; margin-bottom: 20px; }
.dots span { font-size: 32px; color: #ddd; }
.dots span.on { color: #4361ee; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 16px; }
.grid button { height: 60px; font-size: 24px; border-radius: 12px; background: #f0f0f5; display: flex; align-items: center; justify-content: center; }
.grid button:active { background: #ddd; }
.grid .ghost { visibility: hidden; }
.grid .del { background: #ffe0e0; color: #e74c3c; }
.btns { display: flex; gap: 8px; }
.btns b { flex: 1; padding: 12px; border-radius: 12px; font-size: 16px; cursor: pointer; display: block; }
.cancel { background: #f0f0f5; color: #666; font-weight: normal; }
.ok { background: #4361ee; color: #fff; font-weight: bold; }
.ok.off { background: #ccc; }
</style>
