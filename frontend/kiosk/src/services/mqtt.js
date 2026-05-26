import mqtt from 'mqtt'

const MQTT_BROKER = import.meta.env.VITE_MQTT_BROKER || 'mqtt://localhost:1883'
const TOPICS = {
  seatState: (code) => `kiosk/${code}/seat/state`,
  qrIssue: (code) => `kiosk/${code}/qr/issue`,
  doorStatus: (code) => `door/${code}/status`,
  doorEvent: (code) => `door/${code}/event`,
}

let client = null
let listeners = []

export function connectMqtt(roomCode) {
  if (client?.connected) return

  client = mqtt.connect(MQTT_BROKER, {
    clientId: `raydot-kiosk-${roomCode || 'anon'}`,
    clean: true,
    reconnectPeriod: 5000,
    connectTimeout: 4000,
  })

  client.on('connect', () => {
    console.log('[MQTT] Kiosk connected')
    if (roomCode) {
      client.subscribe(TOPICS.seatState(roomCode))
      client.subscribe(TOPICS.qrIssue(roomCode))
      client.subscribe(TOPICS.doorStatus(roomCode))
      client.subscribe(TOPICS.doorEvent(roomCode))
    }
    // Publish kiosk online status (LWT)
    client.publish(`kiosk/${roomCode}/status`, JSON.stringify({ connected: true }), { retain: true })
  })

  client.on('message', (topic, payload) => {
    try {
      const data = JSON.parse(payload.toString())
      listeners.forEach(fn => fn(topic, data))
    } catch (e) {
      console.error('[MQTT] Parse error:', e)
    }
  })

  client.on('close', () => console.log('[MQTT] Disconnected'))
  client.on('error', (e) => console.error('[MQTT] Error:', e))
}

export function disconnectMqtt() {
  if (client) {
    client.end(true)
    client = null
  }
}

export function onMessage(fn) {
  listeners.push(fn)
  return () => { listeners = listeners.filter(f => f !== fn) }
}

export function publish(topic, data) {
  if (client?.connected) {
    client.publish(topic, JSON.stringify(data), { qos: 0, retain: false })
  }
}

export { TOPICS }
