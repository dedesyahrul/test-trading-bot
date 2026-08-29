<template>
  <div class="container">
    <div class="card">
      <div class="card-title">Register</div>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="form-label">Username</label>
          <input v-model="username" type="text" class="form-input" required />
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input v-model="email" type="email" class="form-input" required />
        </div>
        <div class="form-group">
          <label class="form-label">Password</label>
          <input v-model="password" type="password" class="form-input" required />
        </div>
        <button type="submit" class="btn btn-primary">Register</button>
        <router-link to="/login" class="btn btn-secondary">Login</router-link>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/api'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')

const handleRegister = async () => {
  try {
    await authService.register(username.value, email.value, password.value)
    router.push('/login')
  } catch (err) {
    error.value = 'Registration failed'
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
