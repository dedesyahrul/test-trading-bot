<template>
  <div id="app">
    <header v-if="isAuthenticated" class="app-header">
      <router-link to="/" class="brand" @click="menuOpen = false">
        <span class="brand-mark">M</span>
        <span><strong>MemeX</strong><small>TRADING OS</small></span>
      </router-link>
      <button class="menu-toggle" aria-label="Toggle navigation" @click="menuOpen = !menuOpen">MENU</button>
      <nav class="navbar-menu" :class="{ open: menuOpen }">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to" @click="menuOpen = false">
          <span class="nav-index">0{{ item.index }}</span>{{ item.label }}
        </router-link>
        <div class="header-divider" />
        <div class="connection-pill"><span :class="['status-dot', { live: wsConnected }]" />{{ wsConnected ? 'LIVE' : 'OFFLINE' }}</div>
        <button @click="logout" class="btn btn-secondary btn-sm">Logout</button>
      </nav>
    </header>
    <router-view v-slot="{ Component }"><Transition name="page" mode="out-in"><component :is="Component" /></Transition></router-view>
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useWebSocketStore } from './stores/websocket'
import ToastContainer from './components/ToastContainer.vue'

const router = useRouter(); const route = useRoute(); const authStore = useAuthStore(); const wsStore = useWebSocketStore()
const menuOpen = ref(false)
const isAuthenticated = computed(() => Boolean(authStore.token) && !['/login', '/register'].includes(route.path))
const wsConnected = computed(() => wsStore.isConnected)
const navItems = [{ to: '/', label: 'Overview', index: 1 }, { to: '/scanner', label: 'Scanner', index: 2 }, { to: '/positions', label: 'Positions', index: 3 }, { to: '/settings', label: 'Settings', index: 4 }, { to: '/audit', label: 'Audit', index: 5 }]
const logout = () => { authStore.logout(); menuOpen.value = false; router.push('/login') }
</script>

<style scoped>
.app-header { position: sticky; top: 0; z-index: 10; display: flex; align-items: center; justify-content: space-between; min-height: 76px; padding: 0 34px; background: rgba(8,11,18,.82); border-bottom: 1px solid var(--line); backdrop-filter: blur(18px); }
.brand { display: flex; align-items: center; gap: 11px; color: var(--text); text-decoration: none; letter-spacing: -.03em; }
.brand strong { display: block; font-size: 1.08rem; }.brand small { display: block; color: var(--muted); font: 500 .55rem 'DM Mono', monospace; letter-spacing: .15em; }
.brand-mark { display: grid; width: 32px; height: 32px; place-items: center; border-radius: 9px; background: var(--accent); color: #08100a; font-weight: 900; }
.navbar-menu { display: flex; align-items: center; gap: 7px; }.navbar-menu a { padding: 9px 12px; color: var(--muted); border-radius: 8px; font-size: .8rem; font-weight: 700; text-decoration: none; }.navbar-menu a:hover, .navbar-menu a.router-link-active { background: var(--surface-raised); color: var(--text); }.nav-index { margin-right: 7px; color: var(--accent); font: .65rem 'DM Mono', monospace; }
.header-divider { width: 1px; height: 24px; margin: 0 8px; background: var(--line); }.connection-pill { display: flex; align-items: center; gap: 7px; color: var(--muted); font: 500 .67rem 'DM Mono', monospace; }.status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--danger); }.status-dot.live { background: var(--accent); box-shadow: 0 0 10px var(--accent); }.menu-toggle { display: none; background: none; border: 0; color: var(--muted); font: .7rem 'DM Mono', monospace; }
.page-enter-active, .page-leave-active { transition: opacity .18s, transform .18s; }.page-enter-from, .page-leave-to { opacity: 0; transform: translateY(6px); }
@media (max-width: 760px) { .app-header { padding: 0 16px; }.menu-toggle { display: block; }.navbar-menu { position: absolute; top: 76px; right: 0; left: 0; display: none; padding: 14px 16px 18px; background: rgba(8,11,18,.97); border-bottom: 1px solid var(--line); }.navbar-menu.open { display: grid; }.header-divider { display: none; }.connection-pill { margin: 8px 0; } }
</style>
