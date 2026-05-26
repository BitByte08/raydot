import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDashboardStore = defineStore('dashboard', () => {
  const kioskStatuses = ref({})
  const doorStatuses = ref({})
  const seatStates = ref({})
  const stats = ref({
    totalUsers: 0,
    blacklistedUsers: 0,
    activeSeats: 0,
    qrIssuedToday: 0,
    qrUsedToday: 0,
  })

  return { kioskStatuses, doorStatuses, seatStates, stats }
})
