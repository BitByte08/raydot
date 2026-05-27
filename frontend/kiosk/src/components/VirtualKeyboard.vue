<template>
  <div class="vk-overlay" v-if="visible">
    <div class="vk-keyboard">
      <div class="vk-row">
        <button v-for="k in '1234567890'" :key="k" @click="type(k)">{{ k }}</button>
      </div>
      <div class="vk-row">
        <button v-for="k in 'qwertyuiop'" :key="k" @click="type(k)">{{ k }}</button>
      </div>
      <div class="vk-row">
        <button v-for="k in 'asdfghjkl'" :key="k" @click="type(k)">{{ k }}</button>
      </div>
      <div class="vk-row">
        <button class="vk-shift" @click="shift=!shift">↑</button>
        <button v-for="k in getRow3()" :key="k" @click="type(k)">{{ k }}</button>
      </div>
      <div class="vk-row">
        <button class="vk-wide" @click="type(' ')">스페이스</button>
        <button class="vk-back" @click="back">←</button>
        <button class="vk-done" @click="close">완료</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ modelValue: String, visible: Boolean })
const emit = defineEmits(['update:modelValue', 'close'])

const shift = ref(false)
const val = ref(props.modelValue || '')

watch(() => props.visible, (v) => {
  if (v) { val.value = props.modelValue || '' }
})

const row3Base = 'zxcvbnm'
const row3Shift = 'ZXCVBNM'
function getRow3() { return shift.value ? row3Shift : row3Base }

function type(k) {
  val.value += k
  if (shift.value) shift.value = false
  emit('update:modelValue', val.value)
}
function back() {
  val.value = val.value.slice(0, -1)
  emit('update:modelValue', val.value)
}
function close() { emit('close') }
</script>

<style scoped>
.vk-overlay { position: fixed; bottom: 0; left: 0; right: 0; z-index: 999; }
.vk-keyboard { background: #2c2c3a; padding: 6px 4px; border-radius: 8px 8px 0 0; }
.vk-row { display: flex; gap: 3px; justify-content: center; margin-bottom: 3px; }
.vk-row button { flex: 1; max-width: 52px; height: 42px; font-size: 16px; background: #4a4a5e; color: #fff; border-radius: 4px; min-width: 0; min-height: 0; }
.vk-row button:active { background: #666; }
.vk-shift { max-width: 44px !important; }
.vk-wide { flex: 4 !important; max-width: none !important; }
.vk-back { flex: 1.5 !important; max-width: 60px !important; background: #5a4a3a !important; }
.vk-done { flex: 1.5 !important; max-width: 60px !important; background: #4361ee !important; }
</style>
