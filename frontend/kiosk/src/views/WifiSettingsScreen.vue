<template>
  <div class="wifi-screen">
    <div class="header">
      <button class="back-btn" @click="$router.back()">← 뒤로</button>
      <h2>WiFi 설정</h2>
    </div>
    <div class="body">
      <div class="current-status">
        <span class="status-dot" :class="connected ? 'on' : 'off'"></span>
        {{ connected ? `${currentSSID} 연결됨` : '연결 안됨' }}
      </div>
      <button class="scan-btn" @click="scanNetworks" :disabled="scanning">
        {{ scanning ? '스캔 중...' : '네트워크 검색' }}
      </button>
      <div class="network-list">
        <div v-for="net in networks" :key="net.ssid" class="network-item" @click="selectNetwork(net)">
          <span class="net-name">{{ net.ssid }}</span>
          <span class="net-signal">{{ '📶' }}{{ net.signal > 70 ? '●●●' : net.signal > 40 ? '●●' : '●' }}</span>
          <span class="net-secure">{{ net.secure ? '🔒' : '' }}</span>
        </div>
        <p v-if="!scanning && networks.length === 0" class="empty">검색된 네트워크가 없습니다</p>
      </div>
    </div>
    <PinKeypad v-if="showPassword" title="WiFi 비밀번호" v-model="wifiPassword" @confirm="connectNetwork" @cancel="showPassword = false" />
    <div v-if="msg" class="toast">{{ msg }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PinKeypad from '@/components/PinKeypad.vue'

const connected = ref(false)
const currentSSID = ref('')
const scanning = ref(false)
const networks = ref([])
const selectedNetwork = ref(null)
const showPassword = ref(false)
const wifiPassword = ref('')
const msg = ref('')

async function scanNetworks() {
  // In Electron, invoke nmcli via IPC. Mock data for now.
  scanning.value = true; networks.value = []; msg.value = ''
  try {
    if (window.electron) {
      const result = await window.electron.scanWifi()
      networks.value = result.map(n => ({ ssid: n.ssid, signal: n.signal, secure: n.security !== '' }))
    } else {
      // Mock for dev
      setTimeout(() => {
        networks.value = [
          { ssid: 'School-WiFi', signal: 85, secure: true },
          { ssid: 'School-Guest', signal: 60, secure: false },
          { ssid: 'IoT-Network', signal: 75, secure: true },
        ]
      }, 1000)
    }
  } catch(e) { msg.value = 'WiFi 검색 실패' }
  finally { scanning.value = false }
}

function selectNetwork(net) {
  selectedNetwork.value = net
  if (net.secure) { showPassword.value = true } else { connectNetwork() }
}

async function connectNetwork(password) {
  showPassword.value = false; msg.value = `${selectedNetwork.value.ssid} 연결 중...`
  try {
    if (window.electron) {
      await window.electron.connectWifi(selectedNetwork.value.ssid, password || '')
    }
    connected.value = true; currentSSID.value = selectedNetwork.value.ssid
    msg.value = `${selectedNetwork.value.ssid} 연결 완료`
    setTimeout(() => msg.value = '', 2000)
  } catch(e) { msg.value = 'WiFi 연결 실패' }
}

onMounted(() => scanNetworks())
</script>

<style scoped>
.wifi-screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.header { display: flex; align-items: center; padding: 12px 16px; background: #1a1a2e; color: #fff; }
.header h2 { flex: 1; text-align: center; font-size: 20px; }
.back-btn { background: none; color: #fff; font-size: 16px; min-width: 60px; }
.body { flex: 1; padding: 16px; overflow-y: auto; }
.current-status { display: flex; align-items: center; gap: 8px; padding: 12px; background: #fff; border-radius: 8px; margin-bottom: 12px; font-size: 16px; }
.status-dot { width: 12px; height: 12px; border-radius: 50%; }
.status-dot.on { background: #2ecc71; }
.status-dot.off { background: #e74c3c; }
.scan-btn { width: 100%; padding: 14px; background: #4361ee; color: #fff; border-radius: 8px; font-size: 16px; margin-bottom: 12px; }
.scan-btn:disabled { background: #ccc; }
.network-list { background: #fff; border-radius: 8px; overflow: hidden; }
.network-item { display: flex; align-items: center; padding: 14px 16px; border-bottom: 1px solid #eee; font-size: 16px; cursor: pointer; min-height: 52px; }
.network-item:active { background: #f0f0f5; }
.net-name { flex: 1; }
.net-signal { margin-right: 8px; font-size: 12px; }
.empty { text-align: center; color: #999; padding: 24px; }
.toast { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%); background: #333; color: #fff; padding: 10px 24px; border-radius: 8px; font-size: 14px; z-index: 100; }
</style>
