# MemeX — Deployment Architecture

> Dokumen ini memandu bagaimana MemeX di-deploy di environment produksi menggunakan arsitektur berbasis container.

---

## Table of Contents

- [1. Environment Architecture](#1-environment-architecture)
- [2. Component Breakdown](#2-component-breakdown)
- [3. Docker Compose Configuration](#3-docker-compose-configuration)
- [4. CI/CD Pipeline](#4-cicd-pipeline)
- [5. Scaling Strategy](#5-scaling-strategy)

---

## 1. Environment Architecture

MemeX dirancang sebagai aplikasi *cloud-native* 12-factor. Deployment standar dirancang untuk dapat berjalan di VPS mandiri (seperti DigitalOcean, AWS EC2, atau Hetzner) menggunakan Docker dan Docker Compose.

```text
       [Internet]
           |
    (HTTPS / WSS)
           |
   [Reverse Proxy] (Nginx / Traefik / Caddy)
           |
+--------------------------+
|      VPC / Docker Net    |
|                          |
|  [Frontend (Vue)]        |
|  [Backend API]           |
|                          |
|  [Worker: Discovery]     |
|  [Worker: ML Engine]     |
|  [Worker: Execution]     |
|                          |
|  [Redis]                 |
|  [PostgreSQL]            |
+--------------------------+
```

---

## 2. Component Breakdown

| Container / Service | Deskripsi | Port Internal | Expose |
|---------------------|-----------|---------------|--------|
| `proxy` | Meng-handle SSL/TLS termination, routing HTTP ke frontend/API, dan WebSocket. | 80/443 | Yes |
| `frontend` | Menyajikan static assets Vue.js. | 80 | No |
| `api` | FastAPI server yang merespons request dashboard. | 8000 | No |
| `worker-scanner` | ARQ Worker khusus tugas Discovery & Market Data. | - | No |
| `worker-ml` | ARQ Worker khusus Feature Engineering, Risk, & Prediction. | - | No |
| `worker-exec` | ARQ Worker khusus Strategy & Execution. Akses private keys di-inject ke container ini. | - | No |
| `postgres` | Primary relational database. | 5432 | No |
| `redis` | Message broker untuk ARQ, caching, & rate limiting. | 6379 | No |

---

## 3. Docker Compose Configuration

Penggunaan Docker Compose memisahkan worker berdasarkan fungsinya. Ini bertujuan untuk mengisolasi kegagalan (misalnya worker ML yang crash kehabisan memori tidak boleh mengganggu worker eksekusi).

**Rekomendasi Spesifikasi Hardware (Production):**
- CPU: 4 Cores
- RAM: 8 GB (PostgreSQL dan ML inference membutuhkan cukup memori)
- Storage: 100 GB NVMe SSD (Penting untuk read/write database yang cepat)

*(File `docker-compose.yml` terperinci akan dibuat pada fase implementasi kode).*

---

## 4. CI/CD Pipeline

Untuk memastikan proses update yang aman dan cepat:

1. **Lint & Test:** Setiap commit ke branch utama akan men-trigger GitHub Actions / GitLab CI untuk menjalankan *linter* (flake8/black) dan *unit test*.
2. **Build Image:** Image Docker dibangun dan di-push ke Container Registry.
3. **Deployment (Zero Downtime / Rolling Update):**
   - Di production, dianjurkan menggunakan mekanisme rolling update.
   - Migrasi database (Alembic) harus berjalan terlebih dahulu sebelum kontainer backend/worker baru di-*start*.
   - Restart worker harus aman (menunggu/meng-*drain* task yang sedang berjalan jika memungkinkan).

---

## 5. Scaling Strategy

Jika operasi MemeX meluas (memantau ribuan koin dari puluhan chain secara bersamaan):

1. **Horizontal Scaling:**
   - Container `worker-scanner` dan `worker-ml` dapat di-scale ke banyak instance (misal `docker-compose scale worker-scanner=3`). Redis akan mendistribusikan task secara merata.
2. **Vertical Scaling Database:**
   - PostgreSQL dan Redis harus di-upgrade sumber dayanya, atau diganti dengan Managed Database Services (seperti AWS RDS & Elasticache).
3. **Execution Worker Lock:**
   - Container `worker-exec` sebaiknya tetap dibuat *singleton* (atau menggunakan skema distributed lock yang ketat di Redis) untuk menghindari kemungkinan duplicate trade execution.
