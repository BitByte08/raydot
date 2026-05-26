import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const logs = ref([])
  const currentSeat = ref(null)

  function setLogs(logList) {
    logs.value = logList
  }

  function setCurrentSeat(seat) {
    currentSeat.value = seat
  }

  return { logs, currentSeat, setLogs, setCurrentSeat }
})
