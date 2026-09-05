import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

interface User {
  id: string
  username: string
  email: string
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string>('')
  const isAuthenticated = computed(() => !!token.value)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  }

  const setUser = (newUser: User) => {
    user.value = newUser
  }

  const logout = () => {
    user.value = null
    token.value = ''
    localStorage.removeItem('access_token')
    sessionStorage.removeItem('access_token')
    delete axios.defaults.headers.common['Authorization']
  }

  const loadToken = () => {
    const stored = localStorage.getItem('access_token')
    if (stored) {
      setToken(stored)
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    setToken,
    setUser,
    logout,
    loadToken,
  }
})
