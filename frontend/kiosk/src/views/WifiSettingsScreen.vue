<template>
  <div class="wifi-screen">
    <div class="header">
      <button class="back-btn" @click="$router.back()">← 뒤로</button>
      <h2>WiFi 설정</h2>
    </div>
    <div class="body">
      <div class="ip-card">
        <span class="ip-label">IP 주소</span>
        <span class="ip-value">{{ ip || '확인 중...' }}</span>
      </div>
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
          <span class="net-signal">{{ net.signal }}%</span>
          <span class="net-secure">{{ net.secure ? 'PW' : '' }}</span>
        </div>
        <p v-if="!scanning && networks.length === 0" class="empty">검색된 네트워크가 없습니다</p>
      </div>
    </div>
    <div v-if="showPassword" class="pwd-overlay">
      <div class="pwd-box">
        <h3>{{ selectedNetwork?.ssid }} 비밀번호</h3>
        <input v-model="wifiPassword" type="text" placeholder="비밀번호 입력" autofocus />
        <div class="pwd-btns">
          <button class="cancel" @click="showPassword = false; wifiPassword = ''">취소</button>
          <button class="ok" :disabled="!wifiPassword" @click="connectNetwork(wifiPassword)">연결</button>
        </div>
      </div>
    </div>
    <VirtualKeyboard v-model="wifiPassword" :visible="showPassword" @close="showPassword = false" />
    <div v-if="msg" class="toast">{{ msg }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PinKeypad from '@/components/PinKeypad.vue'
import VirtualKeyboard from '@/components/VirtualKeyboard.vue'

const ip = ref('')
const connected = ref(false)
const currentSSID = ref('')
const scanning = ref(false)
const networks = ref([])
const selectedNetwork = ref(null)
const showPassword = ref(false)
const wifiPassword = ref('')
const msg = ref('')

async function getStatus() {
  if (window.electron) {
    try {
      const s = await window.electron.wifiStatus()
      ip.value = await window.electron.getIp()
      connected.value = s.connected
      currentSSID.value = s.ssid || ''
    } catch(e) { ip.value = '확인 불가' }
  }
}

async function scanNetworks() {
  scanning.value = true; networks.value = []; msg.value = ''
  try {
    if (window.electron) {
      const result = await window.electron.scanWifi()
      networks.value = result.map(n => ({ ssid: n.ssid, signal: n.signal, secure: n.security !== '' }))
    } else {
      msg.value = 'WiFi 검색은 데스크톱 앱에서만 가능합니다'
    }
  } catch(e) { msg.value = 'WiFi 검색 실패 - nmcli가 설치되어 있나요?' }
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
      await getStatus()
      msg.value = `${selectedNetwork.value.ssid} 연결 완료`
    }
  } catch(e) { msg.value = 'WiFi 연결 실패' }
  setTimeout(() => msg.value = '', 2000)
}

onMounted(() => { getStatus(); scanNetworks() })
</script>

<style scoped>
.wifi-screen { width: 800px; height: 480px; background: #f5f5f5; display: flex; flex-direction: column; }
.header { display: flex; align-items: center; padding: 6px 12px; background: #1a1a2e; color: #fff; }
.header h2 { flex: 1; text-align: center; font-size: 18px; }
.back-btn { background: none; color: #fff; font-size: 16px; min-width: 50px; }
.body { flex: 1; padding: 10px 12px; overflow-y: auto; }
.ip-card { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #1a1a2e; color: #fff; border-radius: 8px; margin-bottom: 8px; font-size: 15px; }
.ip-label { opacity: 0.7; }
.ip-value { font-weight: bold; font-size: 18px; letter-spacing: 1px; }
.current-status { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff; border-radius: 6px; margin-bottom: 8px; font-size: 14px; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; }
.status-dot.on { background: #2ecc71; }
.status-dot.off { background: #e74c3c; }
.scan-btn { width: 100%; padding: 10px; background: #4361ee; color: #fff; border-radius: 6px; font-size: 15px; margin-bottom: 6px; }
.scan-btn:disabled { background: #ccc; }
.network-list { background: #fff; border-radius: 6px; overflow: hidden; }
.network-item { display: flex; align-items: center; padding: 10px 14px; border-bottom: 1px solid #eee; font-size: 14px; cursor: pointer; min-height: 44px; }
.network-item:active { background: #f0f0f5; }
.net-name { flex: 1; }
.net-signal { margin-right: 6px; font-size: 12px; color: #666; }
.empty { text-align: center; color: #999; padding: 20px; font-size: 14px; }
.toast { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%); background: #333; color: #fff; padding: 8px 20px; border-radius: 6px; font-size: 13px; z-index: 100; }
.pwd-overlay { position: fixed; top: 0; left: 0; right: 0; height: 200px; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 50; }
.pwd-box { background: #fff; border-radius: 10px; padding: 16px 20px; width: 350px; }
.pwd-box h3 { font-size: 16px; margin-bottom: 10px; text-align: center; }
.pwd-box input { width: 100%; font-size: 16px; padding: 8px; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 10px; }
.pwd-btns { display: flex; gap: 8px; }
.pwd-btns button { flex: 1; padding: 8px; border-radius: 6px; font-size: 14px; }
.pwd-btns .cancel { background: #f0f0f5; color: #666; }
.pwd-btns .ok { background: #4361ee; color: #fff; }
.pwd-btns .ok:disabled { background: #ccc; }
</style>
