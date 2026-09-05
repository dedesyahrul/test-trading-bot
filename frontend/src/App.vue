<template>
  <div id="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <template v-if="isAuthenticated">
      <aside class="app-sidebar" :class="{ open: mobileMenuOpen }">
        <div class="sidebar-top">
          <router-link to="/" class="brand" @click="closeMobileMenu">
            <span class="brand-mark"><span></span></span>
            <span class="brand-copy"><strong>meme<span>X</span></strong><small>TRADING OS</small></span>
          </router-link>
          <button class="collapse-button" aria-label="Collapse sidebar" @click="sidebarCollapsed = !sidebarCollapsed">‹</button>
        </div>

        <div class="workspace-switcher">
          <span class="workspace-avatar">M</span>
          <span><strong>main workspace</strong><small>paper environment</small></span>
          <span class="chevron">⌄</span>
        </div>

        <nav class="sidebar-nav" aria-label="Primary navigation">
          <p class="nav-label">Workspace</p>
          <router-link v-for="item in primaryNav" :key="item.to" :to="item.to" class="nav-link" @click="closeMobileMenu">
            <span class="nav-icon" v-html="item.icon"></span><span class="nav-text">{{ item.label }}</span><span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </router-link>
          <p class="nav-label nav-label-spaced">Operate</p>
          <router-link v-for="item in operateNav" :key="item.to" :to="item.to" class="nav-link" @click="closeMobileMenu">
            <span class="nav-icon" v-html="item.icon"></span><span class="nav-text">{{ item.label }}</span><span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </router-link>
        </nav>

        <div class="sidebar-bottom">
          <div class="system-health"><span class="health-dot"></span><span class="nav-text"><strong>All systems operational</strong><small>RPC latency 184ms</small></span></div>
          <router-link to="/settings" class="profile-card" @click="closeMobileMenu"><span class="profile-avatar">{{ username.slice(0, 1).toUpperCase() || 'M' }}</span><span class="nav-text"><strong>{{ username || 'memeX trader' }}</strong><small>Personal account</small></span><span class="more">•••</span></router-link>
        </div>
      </aside>

      <div v-if="mobileMenuOpen" class="sidebar-backdrop" @click="closeMobileMenu"></div>
      <main class="app-main">
        <header class="topbar">
          <button class="mobile-menu-button" aria-label="Open navigation" @click="mobileMenuOpen = true">☰</button>
          <div class="breadcrumbs"><span>Workspace</span><b>/</b><strong>{{ String(route.name || 'Overview') }}</strong></div>
          <div class="topbar-actions">
            <label class="global-search"><span>⌕</span><input v-model="searchQuery" placeholder="Search tokens, pairs..." /><kbd>⌘ K</kbd></label>
            <button class="icon-button" aria-label="Notifications">♢<i></i></button>
            <div class="top-divider"></div>
            <div class="connection-status"><span :class="['status-dot', { live: wsConnected }]" />{{ wsConnected ? 'Live' : 'Offline' }}</div>
            <button class="wallet-button"><span class="wallet-icon">◈</span> Connect wallet</button>
            <button class="user-menu" aria-label="Account menu"><span class="top-avatar">{{ username.slice(0, 1).toUpperCase() || 'M' }}</span><span>⌄</span></button>
          </div>
        </header>
        <router-view v-slot="{ Component }"><Transition name="page" mode="out-in"><component :is="Component" /></Transition></router-view>
      </main>
    </template>
    <router-view v-else v-slot="{ Component }"><Transition name="page" mode="out-in"><component :is="Component" /></Transition></router-view>
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useWebSocketStore } from './stores/websocket'
import ToastContainer from './components/ToastContainer.vue'

const route = useRoute()
const authStore = useAuthStore()
const wsStore = useWebSocketStore()
const sidebarCollapsed = ref(false)
const mobileMenuOpen = ref(false)
const searchQuery = ref('')
const isAuthenticated = computed(() => Boolean(authStore.token) && !['/login', '/register'].includes(route.path))
const wsConnected = computed(() => wsStore.isConnected)
const username = computed(() => authStore.user?.username || 'memeX trader')
const closeMobileMenu = () => { mobileMenuOpen.value = false }

const overviewIcon = '<svg viewBox="0 0 24 24"><path d="M4 13h6V4H4v9Zm10 7h6v-9h-6v9ZM4 20h6v-3H4v3Zm10-12h6V4h-6v4Z"/></svg>'
const scannerIcon = '<svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.2"/><path d="m16 16 4.2 4.2M8.5 10.8h4.6M10.8 8.5v4.6"/></svg>'
const terminalIcon = '<svg viewBox="0 0 24 24"><path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5v-13Z"/><path d="m8 10 2.5 2.5L8 15M12.5 15H16"/></svg>'
const botIcon = '<svg viewBox="0 0 24 24"><rect x="5" y="7" width="14" height="12" rx="3"/><path d="M12 4v3M8.5 12h.01M15.5 12h.01M9 16h6"/></svg>'
const chartIcon = '<svg viewBox="0 0 24 24"><path d="M4 19V5M4 19h16M7 15l3-4 3 2 4-6"/></svg>'
const walletIcon = '<svg viewBox="0 0 24 24"><path d="M5 7.5A2.5 2.5 0 0 1 7.5 5H19v14H7.5A2.5 2.5 0 0 1 5 16.5v-9Z"/><path d="M5 8h11a2 2 0 0 1 2 2v2h-4a2 2 0 0 0 0 4h4v3M14 14h.01"/></svg>'
const bellIcon = '<svg viewBox="0 0 24 24"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4"/></svg>'
const settingsIcon = '<svg viewBox="0 0 24 24"><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z"/><path d="m19 13.5 1.4 1.1-1.8 3.1-1.7-.7a7.6 7.6 0 0 1-1.6.9l-.3 1.8h-3.6l-.3-1.8a7.6 7.6 0 0 1-1.6-.9l-1.7.7-1.8-3.1L5.4 13.5a7 7 0 0 1 0-2.9L4 9.5l1.8-3.1 1.7.7a7.6 7.6 0 0 1 1.6-.9l.3-1.8H13l.3 1.8a7.6 7.6 0 0 1 1.6.9l1.7-.7 1.8 3.1-1.4 1.1a7 7 0 0 1 0 2.9Z"/></svg>'
const primaryNav = [{ to: '/', label: 'Overview', icon: overviewIcon }, { to: '/scanner', label: 'Token scanner', icon: scannerIcon, badge: '24' }, { to: '/positions', label: 'Live terminal', icon: terminalIcon }]
const operateNav = [{ to: '/settings', label: 'Strategy builder', icon: botIcon }, { to: '/watchlist-history', label: 'Watchlist', icon: chartIcon }, { to: '/positions', label: 'Portfolio', icon: walletIcon }, { to: '/audit', label: 'Alerts & activity', icon: bellIcon, badge: '3' }]
</script>
