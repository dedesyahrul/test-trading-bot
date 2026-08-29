# MemeX — Realtime Communication

> Dokumen ini menjelaskan bagaimana data disinkronkan antara backend (FastAPI/Workers) dan frontend (Vue) secara seketika (realtime).

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Technology Choice](#2-technology-choice)
- [3. Architecture Flow](#3-architecture-flow)
- [4. Event Topics](#4-event-topics)
- [5. Client Handling](#5-client-handling)

---

## 1. Overview

Dashboard trading tidak berguna jika pengguna harus merefresh halaman (`F5`) untuk melihat perubahan harga atau order yang baru saja tereksekusi. MemeX menggunakan koneksi persistent untuk mengirim *push notification* berisi perubahan state dari server ke client.

---

## 2. Technology Choice

**Pilihan:** Native WebSockets via FastAPI (`websockets`).

*Alasan:* 
- FastAPI memiliki dukungan native untuk WebSocket berbasis ASGI.
- Tidak memerlukan overhead library tambahan seperti Socket.IO karena aplikasi ini murni one-way data stream (Server ke Client) untuk event-event tertentu, dan request state (Client ke Server) tetap menggunakan HTTP REST.

---

## 3. Architecture Flow

```mermaid
graph LR
    Worker[Any Worker] -->|Publish Event| Redis[Redis Pub/Sub]
    API[FastAPI Server] -->|Subscribe| Redis
    API -->|WebSocket Stream| Client[Vue Frontend]
    
    Client -.->|REST API (Action)| API
```

1. Ketika *Execution Worker* berhasil membeli koin, ia me-record data ke DB dan mempublikasikan JSON event ke channel Redis (misal: `channel:events`).
2. Proses FastAPI memiliki background task yang men-subscribe channel `channel:events`.
3. Setiap kali FastAPI menerima pesan dari Redis, ia akan me-route (broadcast) pesan tersebut ke semua koneksi WebSocket klien yang aktif dan terautentikasi.

---

## 4. Event Topics

Format data yang dikirim melalui WebSocket selalu memiliki struktur standar:
```json
{
  "topic": "STRING",
  "payload": { ... }
}
```

Daftar Topic Wajib:

| Topic | Deskripsi Payload |
|-------|-------------------|
| `NEW_TOKEN_DISCOVERED` | Token baru lolos risk filter awal. Berisi symbol, address, dan initial liquidity. |
| `MARKET_PRICE_UPDATED` | Tick harga baru untuk token yang ada di watchlist/open positions. |
| `SIGNAL_GENERATED` | Strategi menghasilkan signal (terutama BUY). |
| `ORDER_STATUS_CHANGED` | Perubahan state order (PENDING -> CONFIRMED -> FAILED). |
| `POSITION_UPDATED` | Perubahan unrealized PnL pada posisi yang sedang terbuka. |
| `SYSTEM_ALERT` | Pesan error atau peringatan sistem (misal RPC gagal). |

---

## 5. Client Handling

Di sisi Vue Frontend (melalui composable `useWebSocket`), client harus mengimplementasikan:

1. **Auto-Reconnect:** Jika koneksi terputus (karena proxy restart atau koneksi internet tidak stabil), client akan mencoba reconnect dengan exponential backoff (1s, 2s, 4s...).
2. **State Reconciliation:** Setelah berhasil reconnect, client mungkin melewatkan beberapa event. Client harus melakukan pemanggilan REST API (misalnya `GET /api/v1/positions/open`) untuk men-sinkronisasi ulang *state* terbaru, sebelum mengandalkan WebSocket kembali.
3. **Authentication:** Token JWT harus dikirim saat handshake WebSocket (biasanya melalui query parameter atau pesan inisiasi pertama) untuk memastikan hanya admin yang menerima aliran data sensitif.
