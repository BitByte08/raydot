import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(null)
  const user = ref(null)
  const isLoggedIn = ref(false)

  // Separate session for info/logs/password screens (StudentGate).
  // Lives independently from the DeskScreen check-in session so that
  // navigating between 내 정보 → 이용 기록 doesn't re-prompt login.
  const infoUser = ref(null)
  const infoToken = ref('')
  const infoLoggedIn = computed(() => !!infoUser.value)

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

  function setInfoUser(userData, authToken) {
    infoUser.value = userData
    infoToken.value = authToken
  }

  function clearInfo() {
    infoUser.value = null
    infoToken.value = ''
  }

  return { token, user, isLoggedIn, setUser, logout,
           infoUser, infoToken, infoLoggedIn, setInfoUser, clearInfo }
})
