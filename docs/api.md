# MemeX — REST API Specification

> Dokumen ini mendefinisikan rute dan kontrak data untuk Backend API (FastAPI) yang digunakan oleh Frontend Dashboard.

---

## Table of Contents

- [1. Principles](#1-principles)
- [2. Endpoints Overview](#2-endpoints-overview)
- [3. Authentication](#3-authentication)
- [4. Response Format](#4-response-format)

---

## 1. Principles

- **RESTful:** Menggunakan standar HTTP verbs (GET, POST, PUT, DELETE).
- **Stateless:** Autentikasi berbasis JWT.
- **Pagination:** Semua endpoint yang mengembalikan list harus menggunakan pagination (limit, offset).
- **Documentation:** Semua endpoint terdaftar secara otomatis di OpenAPI/Swagger (`/docs`).

---

## 2. Endpoints Overview

Berikut adalah *domain area* utama dari API.

### 2.1. Authentication (`/api/v1/auth`)
- `POST /login` - Menerima username/password, mengembalikan JWT token.
- `POST /refresh` - Me-refresh access token.
- `GET /me` - Mendapatkan profile user yang sedang login.

### 2.2. Market & Discovery (`/api/v1/market`)
- `GET /tokens` - List watched/active tokens (dengan filter by chain/age).
- `GET /tokens/{address}` - Detail sebuah token termasuk metadata.
- `GET /pairs/{pair_id}/ohlcv` - Mendapatkan data historical chart.

### 2.3. Trading & Positions (`/api/v1/trading`)
- `GET /positions` - List open positions. Filter `?status=OPEN&mode=LIVE`.
- `GET /positions/{id}` - Detail posisi (entry, exit, current price, unrealized PnL).
- `GET /trades` - List closed positions (trade history).
- `POST /positions/{id}/close` - Action manual untuk menutup posisi secara paksa (Market Sell).

### 2.4. System Control (`/api/v1/system`)
- `GET /status` - Mengembalikan status bot (RUNNING, PAUSED, EMERGENCY_STOP).
- `POST /kill-switch` - Mengaktifkan emergency stop.
- `POST /resume` - Menonaktifkan emergency stop (melanjutkan sistem).
- `GET /workers` - Mendapatkan status kesehatan ARQ workers.

### 2.5. Configuration (`/api/v1/config`)
- `GET /strategy` - Mengambil parameter strategi saat ini.
- `PUT /strategy` - Memperbarui parameter (contoh: max_slippage, allocation_size).

---

## 3. Authentication

Header yang dibutuhkan:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

Jika token invalid atau kedaluwarsa, API akan merespons:
```json
{
  "error": "Unauthorized",
  "message": "Token expired"
}
```
(Status Code: 401)

---

## 4. Response Format

Format respons konsisten untuk mempermudah handling di frontend.

**Success Response (2xx):**
```json
{
  "data": {
    "id": "123",
    "name": "Token"
  },
  "meta": {
    "total": 1,
    "page": 1
  }
}
```

**Error Response (4xx, 5xx):**
```json
{
  "error": "ValidationError",
  "message": "Amount exceeds maximum allowed allocation.",
  "details": [
    {
      "field": "amount",
      "issue": "must be less than 10"
    }
  ]
}
```
