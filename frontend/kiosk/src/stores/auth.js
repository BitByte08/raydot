import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(null)
  const user = ref(null)
  const isLoggedIn = ref(false)

  function setUser(userData, authToken) {
    user.value = userData
    token.value = authToken
    isLoggedIn.value = true
  }

  function logout() {
    token.value = null
    user.value = null
    isLoggedIn.value = false
  }

  return { token, user, isLoggedIn, setUser, logout }
})
