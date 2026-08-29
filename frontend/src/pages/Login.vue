<template>
  <div class="container">
    <div class="card">
      <div class="card-title">Login</div>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">Username</label>
          <input v-model="username" type="text" class="form-input" required />
        </div>
        <div class="form-group">
          <label class="form-label">Password</label>
          <input v-model="password" type="password" class="form-input" required />
        </div>
        <button type="submit" class="btn btn-primary">Login</button>
        <router-link to="/register" class="btn btn-secondary">Register</router-link>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authService } from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const error = ref('')

const handleLogin = async () => {
  try {
    const response = await authService.login(username.value, password.value)
    authStore.setToken(response.data.access_token)
    const userResponse = await authService.getCurrentUser()
    authStore.setUser(userResponse.data)
    router.push('/')
  } catch (err) {
    error.value = 'Invalid credentials'
  }
}
</script>

<style scoped>
.btn-secondary {
  background-color: #6c757d;
  color: white;
  margin-left: 1rem;
}

.btn-secondary:hover {
  background-color: #5a6268;
}
</style>
