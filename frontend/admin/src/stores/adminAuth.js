import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAdminAuthStore = defineStore('adminAuth', () => {
  const token = ref(localStorage.getItem('admin_token'))
  const admin = ref(null)

  function setAdmin(adminData, authToken) {
    admin.value = adminData
    token.value = authToken
    localStorage.setItem('admin_token', authToken)
  }

  function logout() {
    token.value = null
    admin.value = null
    localStorage.removeItem('admin_token')
  }

  return { token, admin, setAdmin, logout }
})
