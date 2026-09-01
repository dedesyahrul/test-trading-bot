<template>
  <div class="container">
    <div class="page-header">
      <div>
        <div class="eyebrow">Security / Traceability</div>
        <h1 class="page-title">Audit log</h1>
        <p class="page-subtitle">A chronological record of account, bot, watchlist, and trading actions.</p>
      </div>
      <button class="btn btn-secondary" @click="loadLogs" :disabled="loading">{{ loading ? 'Loading...' : 'Refresh' }}</button>
    </div>
    <div class="card">
      <div class="filters">
        <input v-model="action" class="form-input" placeholder="Filter action, e.g. LOGIN" @keyup.enter="loadLogs" />
        <input v-model="resource" class="form-input" placeholder="Filter resource, e.g. BOT" @keyup.enter="loadLogs" />
        <button class="btn btn-primary" @click="loadLogs">Apply filters</button>
      </div>
      <div v-if="loading" class="loading"><div class="spinner"></div>Loading audit events...</div>
      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-else-if="logs.length === 0" class="alert">No audit events found.</div>
      <div v-else class="audit-list">
        <article v-for="entry in logs" :key="entry.id" class="audit-entry">
          <div class="audit-marker"></div>
          <div class="audit-main"><div class="audit-top"><strong>{{ entry.action }}</strong><span class="badge badge-info">{{ entry.resource }}</span></div><div class="audit-meta">{{ formatDate(entry.created_at) }}<span v-if="entry.resource_id"> · {{ entry.resource_id }}</span></div><pre v-if="Object.keys(entry.details || {}).length">{{ JSON.stringify(entry.details, null, 2) }}</pre></div>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { auditService } from '../services/api'

interface AuditEntry { id: string; action: string; resource: string; resource_id?: string; details: Record<string, unknown>; created_at: string }
const logs = ref<AuditEntry[]>([]); const loading = ref(false); const error = ref(''); const action = ref(''); const resource = ref('')
const formatDate = (value: string) => new Date(value).toLocaleString()
const loadLogs = async () => { loading.value = true; error.value = ''; try { const response = await auditService.list(action.value || undefined, resource.value || undefined); logs.value = response.data.logs } catch (err: any) { error.value = err.response?.data?.detail || 'Failed to load audit log' } finally { loading.value = false } }
onMounted(loadLogs)
</script>

<style scoped>
.filters { display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px; margin-bottom: 22px; }.audit-list { border-left: 1px solid var(--line); margin-left: 7px; }.audit-entry { position: relative; display: flex; gap: 16px; padding: 0 0 24px 22px; }.audit-marker { position: absolute; left: -5px; top: 3px; width: 9px; height: 9px; border: 2px solid var(--accent); border-radius: 50%; background: var(--bg); }.audit-main { width: 100%; }.audit-top { display: flex; align-items: center; gap: 9px; }.audit-meta { margin-top: 3px; color: var(--muted); font: .68rem 'DM Mono', monospace; }.audit-main pre { overflow-x: auto; margin: 10px 0 0; padding: 10px; background: var(--surface-raised); border-radius: 8px; color: var(--muted); font: .7rem 'DM Mono', monospace; }
@media (max-width: 700px) { .filters { grid-template-columns: 1fr; } }
</style>
