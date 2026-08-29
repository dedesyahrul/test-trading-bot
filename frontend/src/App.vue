<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-brand">MemeX</div>
      <div class="navbar-menu">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/scanner">Scanner</router-link>
        <router-link to="/positions">Positions</router-link>
        <router-link to="/settings">Settings</router-link>
        <button @click="logout" class="btn-logout">Logout</button>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #1a1a1a;
  color: white;
  padding: 1rem;
  border-bottom: 1px solid #333;
}

.navbar-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.navbar-menu {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.navbar-menu a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.navbar-menu a:hover {
  background-color: #333;
}

.btn-logout {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-logout:hover {
  background-color: #c82333;
}
</style>
