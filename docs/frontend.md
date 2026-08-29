# MemeX — Frontend Architecture

> Dokumen ini memandu pengembangan dashboard frontend untuk mengelola dan memonitor bot MemeX.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Tech Stack](#2-tech-stack)
- [3. Application Structure](#3-application-structure)
- [4. Core Views](#4-core-views)
- [5. State Management](#5-state-management)

---

## 1. Overview

Frontend MemeX adalah Control Center bagi operator. Ini bukan public-facing app untuk retail user, melainkan *internal tool* berdesain profesional (dark mode, dense data, low latency) bergaya terminal/trading terminal (mirip Bloomberg Terminal atau tradingview).

Fokus utama frontend:
- Visualisasi data secara realtime tanpa perlu reload halaman.
- Konfigurasi parameter risiko dan strategi.
- Kontrol manual (Emergency Stop, Panic Sell).

---

## 2. Tech Stack

- **Framework:** Vue 3 (Composition API, `<script setup>`)
- **Language:** TypeScript (Strict mode)
- **Build Tool:** Vite
- **Styling:** Tailwind CSS (Konfigurasi warna kustom untuk Dark Theme dominan)
- **State Management:** Pinia
- **Routing:** Vue Router
- **Realtime:** Socket.IO Client / native WebSocket
- **Charting:** Lightweight Charts (by TradingView) atau ECharts untuk rendering OHLCV dan volume profile yang cepat.

---

## 3. Application Structure

```text
src/
├── assets/          # Logo, icon, global css
├── components/      # Reusable UI (Button, Modal, DataGrid, StatusBadge)
├── composables/     # Vue 3 custom hooks (useWebSocket, useAuth)
├── layouts/         # Layout wrapper (DashboardLayout, AuthLayout)
├── router/          # Route definitions
├── services/        # API clients (axios instance)
├── stores/          # Pinia stores (auth, positions, market)
├── types/           # TS Interfaces
├── views/           # Page components
└── App.vue
```

---

## 4. Core Views

### 4.1. Main Dashboard (`/`)
- **Top Bar:** Total Balance, Today's PnL, Global Bot Status (Running/Paused), Kill Switch Button.
- **Left Panel (Market Radar):** Daftar token yang baru ditemukan beserta Risk Score dan ML Probability. Realtime update via WebSocket.
- **Center Panel (Charts):** Chart Lightweight dari token yang sedang dipilih, dengan marker (titik entry/exit dari bot).
- **Bottom Panel (Positions):** Datagrid berisi Open Positions (Paper & Live), unrealized PnL, dan aksi manual (Close).

### 4.2. Strategy Configuration (`/strategy`)
- Form untuk mengubah parameter per strategi.
- Input untuk mengaktifkan/menonaktifkan model ML tertentu.
- Pengaturan Slippage Tolerance dan Base Allocation Size.

### 4.3. Trading History (`/history`)
- Tabel riwayat transaksi yang sudah selesai (Closed positions).
- Filter berdasarkan tanggal, token, hasil (Win/Loss), dan mode (Live/Paper).
- Metrik performa (Win Rate, Total Profit).

### 4.4. System Logs (`/logs`)
- Live streaming log dari server. Berguna untuk memantau status worker dan error.

---

## 5. State Management

Pinia digunakan untuk global state:

- `useAuthStore`: Menyimpan JWT token dan status login.
- `useBotStateStore`: Menyimpan status bot (sedang berjalan, emergency stop) dan sinkronisasi dengan server.
- `usePositionsStore`: Menampung list open position. State ini di-*patch* setiap kali ada event WebSocket `POSITION_UPDATED` untuk menghindari fetch ulang via REST API berulang kali.
