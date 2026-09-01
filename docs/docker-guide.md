# MemeX — Panduan Docker: Build & Maintenance

> Dokumen ini menjelaskan cara membangun, menjalankan, memelihara, dan memecahkan masalah deployment MemeX menggunakan Docker dan Docker Compose.

---

## Table of Contents

- [1. Prasyarat](#1-prasyarat)
- [2. Arsitektur Container](#2-arsitektur-container)
- [3. Struktur File Docker](#3-struktur-file-docker)
- [4. Konfigurasi Environment](#4-konfigurasi-environment)
- [5. Port Registry](#5-port-registry)
- [6. Development — Build & Run](#6-development--build--run)
- [7. Production — Build & Run](#7-production--build--run)
- [8. Database Migration](#8-database-migration)
- [9. Operasi Harian (Maintenance)](#9-operasi-harian-maintenance)
- [10. Backup & Restore](#10-backup--restore)
- [11. Update & Rolling Restart](#11-update--rolling-restart)
- [12. Monitoring & Health Check](#12-monitoring--health-check)
- [13. Troubleshooting](#13-troubleshooting)
- [14. Keamanan](#14-keamanan)
- [15. Checklist Deployment](#15-checklist-deployment)

---

## 1. Prasyarat

### Software yang Diperlukan

| Software | Versi Minimum | Cek Versi |
|----------|---------------|-----------|
| Docker Engine | 24.x | `docker --version` |
| Docker Compose | 2.x | `docker compose version` |
| Git | 2.x | `git --version` |

### Spesifikasi Hardware

| Environment | CPU | RAM | Storage |
|-------------|-----|-----|---------|
| Development | 2 core | 4 GB | 20 GB |
| Production | 4 core | 8 GB | 100 GB NVMe SSD |

### Clone Repository

```bash
git clone <repo-url> memex
cd memex
```

---

## 2. Arsitektur Container

```
                    [Internet / Browser]
                            |
              +-------------+-------------+
              |                           |
        :13456 (frontend)           :17845 (backend API)
              |                           |
    +---------+---------------------------+---------+
    |              memex-network (bridge)          |
    |                                              |
    |  [frontend]  [backend]  [worker]             |
    |       |           |          |               |
    |       +-----------+----------+               |
    |                   |                          |
    |            [postgres]  [redis]               |
  +------------------------------------------------+
```

### Daftar Service

| Service | Container Name | Image / Build | Fungsi |
|---------|----------------|---------------|--------|
| `postgres` | `memex-postgres` | `postgres:16-alpine` | Database utama |
| `redis` | `memex-redis` | `redis:7-alpine` | Queue ARQ, cache, Pub/Sub |
| `backend` | `memex-backend` | `infrastructure/docker/backend.Dockerfile` | FastAPI REST + WebSocket |
| `worker` | `memex-worker` | `infrastructure/docker/worker.Dockerfile` | Background jobs (ARQ) |
| `frontend` | `memex-frontend` | `infrastructure/docker/frontend.Dockerfile` | Vue 3 dashboard |

---

## 3. Struktur File Docker

```
memex/
├── docker-compose.yml              # Development (hot-reload, volume mount)
├── docker-compose.prod.yml         # Production (restart policy, healthcheck)
├── .env.example                    # Template environment variables
├── .env                            # Development env (jangan commit!)
├── .env.production                 # Production env (jangan commit!)
└── infrastructure/
    └── docker/
        ├── backend.Dockerfile      # Python 3.12 + FastAPI
        ├── worker.Dockerfile       # Python 3.12 + ARQ worker
        └── frontend.Dockerfile     # Node 20 + Vite
```

### Perbedaan Compose File

| Aspek | `docker-compose.yml` | `docker-compose.prod.yml` |
|-------|----------------------|---------------------------|
| Tujuan | Development lokal | Production / staging |
| Hot reload | ✅ (`--reload` pada backend) | ❌ |
| Volume mount source code | ✅ | ✅ (bisa dihapus untuk immutable image) |
| `restart` policy | Tidak ada | `unless-stopped` |
| Health check | Postgres & Redis saja | Semua service utama |
| Environment | Hardcoded default | Dari `.env` / `.env.production` |
| Redis persistence | Default | AOF (`appendonly yes`) |

---

## 4. Konfigurasi Environment

### Langkah Awal

```bash
# Development
cp .env.example .env

# Production
cp .env.example .env.production
# Edit nilai production (lihat tabel di bawah)
```

### Variabel Environment

| Variabel | Wajib | Default | Deskripsi |
|----------|-------|---------|-----------|
| `SECRET_KEY` | ✅ (prod) | - | JWT signing key. Generate: `openssl rand -hex 32` |
| `DEBUG` | - | `false` | `true` hanya untuk development |
| `ENVIRONMENT` | - | `development` | `production` / `staging` / `development` |
| `TRADING_MODE` | - | `PAPER` | `PAPER` atau `LIVE` |
| `DATABASE_URL` | - | `postgresql://memex:memex@postgres:5432/memex` | URL DB internal Docker (hostname `postgres`) |
| `REDIS_URL` | - | `redis://redis:6379/0` | URL Redis internal Docker (hostname `redis`) |
| `DB_PORT` | - | `15487` | Host port PostgreSQL |
| `REDIS_PORT` | - | `16721` | Host port Redis |
| `BACKEND_PORT` | - | `17845` | Host port backend API |
| `FRONTEND_PORT` | - | `13456` | Host port frontend |
| `VITE_API_URL` | - | `http://localhost:17845/api` | URL API untuk frontend |
| `VITE_WS_URL` | - | `ws://localhost:17845/ws` | URL WebSocket untuk frontend |
| `DB_USER` | - | `memex` | Username PostgreSQL (prod compose) |
| `DB_PASSWORD` | ✅ (prod) | `memex` | Password PostgreSQL |
| `DB_NAME` | - | `memex` | Nama database |

> **PENTING:** Jangan pernah commit file `.env` atau `.env.production` ke Git. Private key wallet **tidak boleh** disimpan di file env yang di-commit.

### Contoh `.env` Production

```env
SECRET_KEY=<generate-dengan-openssl-rand-hex-32>
DEBUG=false
ENVIRONMENT=production
TRADING_MODE=PAPER

DB_USER=memex
DB_PASSWORD=<password-kuat>
DB_NAME=memex
DB_PORT=15487

REDIS_PORT=16721
BACKEND_PORT=17845
FRONTEND_PORT=13456

VITE_API_URL=https://api.example.com/api
VITE_WS_URL=wss://api.example.com/ws
```

---

## 5. Port Registry

### Port Registry (MemeX)

| Service | Container Port | Host Port | Protocol |
|---------|---------------:|----------:|----------|
| Frontend | 3000 | **13456** | TCP |
| Backend API | 8000 | **17845** | TCP |
| PostgreSQL | 5432 | **15487** | TCP |
| Redis | 6379 | **16721** | TCP |
| WebSocket | 8000 | **17845** | WS |

> Port dipilih setelah availability check pada host development. Container port internal **tidak diubah** — hanya host port yang di-map ke angka non-default agar tidak bentrok dengan service lain (3000, 5432, 6379, 8000 sudah digunakan di host ini).

> **Catatan:** Container port internal **tidak perlu diubah**. Hanya host port yang disesuaikan jika terjadi konflik.

### Cek Port Sebelum Start

**Windows (PowerShell):**
```powershell
netstat -ano | findstr ":17845"
netstat -ano | findstr ":15487"
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

**Linux / macOS:**
```bash
ss -tlnp | grep -E ':(17845|15487|16721|13456)'
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

Jika port sudah digunakan, ubah nilai di `.env` lalu restart compose.

---

## 6. Development — Build & Run

### 6.1 Persiapan Frontend (Pertama Kali)

Frontend Dockerfile menggunakan `npm ci` yang membutuhkan `package-lock.json`. Generate terlebih dahulu:

```bash
cd frontend
npm install
cd ..
```

### 6.2 Build Semua Image

```bash
# Dari root project
docker compose build

# Build service tertentu saja
docker compose build backend
docker compose build worker
docker compose build frontend
```

### 6.3 Jalankan Infrastruktur Saja (DB + Redis)

```bash
docker compose up -d postgres redis
```

Tunggu hingga healthy:
```bash
docker compose ps
```

### 6.4 Jalankan Semua Service

```bash
docker compose up -d
```

Atau dengan log realtime:
```bash
docker compose up
```

### 6.5 Jalankan Database Migration

```bash
docker compose exec backend alembic upgrade head
```

### 6.6 Verifikasi

| Endpoint | URL | Expected |
|----------|-----|----------|
| API Health | http://localhost:17845/api/health | `{"status":"ok"}` |
| API Docs | http://localhost:17845/docs | Swagger UI |
| App Health | http://localhost:17845/health | `{"status":"healthy"}` |
| Frontend | http://localhost:13456 | Dashboard Vue |
| WebSocket | ws://localhost:17845/ws | Koneksi WS aktif |

```bash
# Cek health via CLI
curl http://localhost:17845/api/health
curl http://localhost:17845/health
```

### 6.7 Stop & Hapus Container

```bash
# Stop semua service (data volume tetap ada)
docker compose down

# Stop + hapus volume (HATI-HATI: data DB hilang!)
docker compose down -v
```

---

## 7. Production — Build & Run

### 7.1 Persiapan

```bash
# 1. Siapkan environment production
cp .env.example .env.production
# Edit .env.production — set SECRET_KEY, DB_PASSWORD, dll.

# 2. Generate package-lock.json (jika belum ada)
cd frontend && npm install && cd ..

# 3. Cek port availability (lihat Section 5)
```

### 7.2 Build Image Production

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production build --no-cache
```

### 7.3 Start Services

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### 7.4 Migration (Wajib Sebelum Traffic)

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend alembic upgrade head
```

### 7.4 Verifikasi Production

```bash
docker compose -f docker-compose.prod.yml ps

# Semua service harus "healthy" atau "running"
docker compose -f docker-compose.prod.yml logs --tail=50 backend
docker compose -f docker-compose.prod.yml logs --tail=50 worker
```

### 7.5 Reverse Proxy (Rekomendasi)

Jangan expose PostgreSQL dan Redis ke internet. Gunakan reverse proxy (Nginx/Caddy/Traefik) di depan frontend dan backend:

```
Internet → HTTPS :443 → [Nginx/Caddy]
                          ├── /      → frontend:3000
                          ├── /api   → backend:8000
                          └── /ws    → backend:8000 (WebSocket upgrade)
```

---

## 8. Database Migration

### Jalankan Migration

```bash
# Development
docker compose exec backend alembic upgrade head

# Production
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend alembic upgrade head
```

### Cek Status Migration

```bash
docker compose exec backend alembic current
docker compose exec backend alembic history
```

### Rollback (Hati-hati!)

```bash
# Rollback 1 langkah
docker compose exec backend alembic downgrade -1

# Rollback ke revision tertentu
docker compose exec backend alembic downgrade 001_initial
```

### Buat Migration Baru (Development)

```bash
docker compose exec backend alembic revision --autogenerate -m "deskripsi_perubahan"
```

> Selalu review file migration yang di-generate sebelum `upgrade head`.

---

## 9. Operasi Harian (Maintenance)

### 9.1 Melihat Status Container

```bash
docker compose ps
docker compose -f docker-compose.prod.yml ps
```

### 9.2 Melihat Logs

```bash
# Semua service (follow realtime)
docker compose logs -f

# Service tertentu
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f postgres

# 100 baris terakhir
docker compose logs --tail=100 backend

# Production
docker compose -f docker-compose.prod.yml logs -f --tail=200 worker
```

### 9.3 Restart Service

```bash
# Restart satu service
docker compose restart backend
docker compose restart worker

# Restart semua
docker compose restart

# Production — rolling restart (satu per satu)
docker compose -f docker-compose.prod.yml restart worker
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
```

### 9.4 Masuk ke Container (Shell)

```bash
# Backend shell
docker compose exec backend bash

# PostgreSQL CLI
docker compose exec postgres psql -U memex -d memex

# Redis CLI
docker compose exec redis redis-cli
```

### 9.5 Cek Penggunaan Resource

```bash
docker stats

# Disk usage
docker system df
docker volume ls
```

### 9.6 Bersihkan Resource Tidak Terpakai

```bash
# Hapus container yang stopped
docker container prune

# Hapus image tidak terpakai
docker image prune

# Hapus semua (HATI-HATI)
docker system prune -a
```

> **Jangan** jalankan `docker system prune -a --volumes` di production tanpa backup — akan menghapus volume database.

---

## 10. Backup & Restore

### 10.1 Backup PostgreSQL

```bash
# Buat direktori backup
mkdir -p backups

# Dump database
docker compose exec postgres pg_dump -U memex -d memex -F c -f /tmp/memex_backup.dump

# Copy ke host
docker cp memex-postgres:/tmp/memex_backup.dump ./backups/memex_$(date +%Y%m%d_%H%M%S).dump
```

**Windows (PowerShell):**
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker compose exec postgres pg_dump -U memex -d memex -F c -f /tmp/memex_backup.dump
docker cp memex-postgres:/tmp/memex_backup.dump "./backups/memex_$timestamp.dump"
```

### 10.2 Restore PostgreSQL

```bash
# Stop backend & worker dulu agar tidak ada koneksi aktif
docker compose stop backend worker

# Copy dump ke container
docker cp ./backups/memex_backup.dump memex-postgres:/tmp/restore.dump

# Restore (akan overwrite data existing!)
docker compose exec postgres pg_restore -U memex -d memex --clean --if-exists /tmp/restore.dump

# Start kembali
docker compose start backend worker
```

### 10.3 Backup Redis (Opsional)

```bash
docker compose exec redis redis-cli BGSAVE
docker cp memex-redis:/data/dump.rdb ./backups/redis_$(date +%Y%m%d).rdb
```

### 10.4 Jadwal Backup Otomatis (Cron — Linux)

```bash
# Tambahkan ke crontab (backup harian jam 02:00)
0 2 * * * cd /path/to/memex && docker compose exec -T postgres pg_dump -U memex -d memex -F c > /backups/memex_$(date +\%Y\%m\%d).dump
```

---

## 11. Update & Rolling Restart

### Prosedur Update Aman (Production)

```bash
# 1. Backup database
# (lihat Section 10.1)

# 2. Pull kode terbaru
git pull origin master

# 3. Rebuild image
docker compose -f docker-compose.prod.yml --env-file .env.production build

# 4. Jalankan migration SEBELUM restart backend
docker compose -f docker-compose.prod.yml --env-file .env.production run --rm backend alembic upgrade head

# 5. Rolling restart — worker dulu, backend, frontend terakhir
docker compose -f docker-compose.prod.yml --env-file .env.production up -d worker
docker compose -f docker-compose.prod.yml --env-file .env.production up -d backend
docker compose -f docker-compose.prod.yml --env-file .env.production up -d frontend

# 6. Verifikasi
docker compose -f docker-compose.prod.yml ps
curl http://localhost:17845/api/health
```

### Rebuild Satu Service Saja

```bash
docker compose build backend
docker compose up -d backend
```

### Force Recreate Container

```bash
docker compose up -d --force-recreate backend
```

---

## 12. Monitoring & Health Check

### Health Check Endpoints

| Service | Endpoint / Command | Expected |
|---------|-------------------|----------|
| Backend API | `GET /api/health` | `{"status":"ok"}` |
| Backend App | `GET /health` | `{"status":"healthy"}` |
| PostgreSQL | `pg_isready -U memex` | `accepting connections` |
| Redis | `redis-cli ping` | `PONG` |
| Frontend | `GET /` port 13456 (host) | HTTP 200 |

### Cek Health Docker

```bash
docker compose ps
# Kolom STATUS menampilkan (healthy) jika healthcheck pass

docker inspect --format='{{.State.Health.Status}}' memex-backend
docker inspect --format='{{.State.Health.Status}}' memex-postgres
```

### Monitor Worker (ARQ)

```bash
docker compose logs -f worker | grep -E "worker|cron|ERROR"
```

### Monitor WebSocket & Redis Pub/Sub

```bash
# Subscribe ke channel events
docker compose exec redis redis-cli SUBSCRIBE channel:events
```

---

## 13. Troubleshooting

### Port Already Allocated

**Gejala:**
```
Error: bind: address already in use
```

**Solusi:**
1. Identifikasi proses: `netstat -ano | findstr :17845` (Windows) atau `ss -tlnp | grep 17845` (Linux)
2. Ubah port di `.env` (misalnya `BACKEND_PORT=18234`)
3. Recreate: `docker compose up -d --force-recreate backend`

---

### Container Exit / Restart Loop

**Diagnosa:**
```bash
docker compose ps
docker compose logs --tail=100 <service-name>
```

**Penyebab umum:**
| Service | Penyebab | Solusi |
|---------|----------|--------|
| `backend` | DB belum ready | Tunggu postgres healthy, lalu restart backend |
| `backend` | Migration belum dijalankan | `alembic upgrade head` |
| `backend` | `SECRET_KEY` kosong (prod) | Set di `.env.production` |
| `worker` | Redis/DB unreachable | Cek `DATABASE_URL`, `REDIS_URL` |
| `frontend` | `package-lock.json` tidak ada | Jalankan `npm install` di folder frontend |
| `postgres` | Port 15487 bentrok | Ubah `DB_PORT` di `.env` |

---

### Database Connection Refused

**Gejala:** Backend log menampilkan `Connection refused` ke postgres.

**Solusi:**
```bash
# Pastikan postgres healthy
docker compose ps postgres

# Test koneksi dari backend container
docker compose exec backend python -c "
import os; print(os.getenv('DATABASE_URL'))
"

# Restart postgres lalu backend
docker compose restart postgres
sleep 5
docker compose restart backend
```

> Di Docker Compose, hostname database adalah `postgres` (nama service), **bukan** `localhost`.

---

### Migration Gagal

```bash
# Cek revision saat ini
docker compose exec backend alembic current

# Lihat history
docker compose exec backend alembic history --verbose

# Jika stuck, cek tabel alembic_version di DB
docker compose exec postgres psql -U memex -d memex -c "SELECT * FROM alembic_version;"
```

---

### Frontend Tidak Bisa Akses API

**Gejala:** CORS error atau network error di browser.

**Solusi:**
1. Pastikan `VITE_API_URL` benar di environment frontend
2. Untuk production dengan domain berbeda, set CORS di backend (`app/main.py`)
3. Rebuild frontend setelah ubah env:
   ```bash
   docker compose up -d --force-recreate frontend
   ```

---

### Worker Tidak Berjalan / Tidak Collect Data

```bash
# Cek log worker
docker compose logs -f worker

# Pastikan worker terdaftar dengan benar
docker compose exec worker python -c "from app.workers.main import WorkerSettings; print(WorkerSettings.functions)"

# Restart worker
docker compose restart worker
```

---

### WebSocket Terputus

1. Cek backend running: `curl http://localhost:17845/health`
2. Cek Redis Pub/Sub: `docker compose exec redis redis-cli PING`
3. Pastikan `VITE_WS_URL` mengarah ke backend yang benar
4. Jika di belakang reverse proxy, pastikan WebSocket upgrade di-enable

---

### Disk Penuh

```bash
docker system df

# Hapus build cache
docker builder prune

# Hapus log container (Linux)
truncate -s 0 $(docker inspect --format='{{.LogPath}}' memex-backend)
```

---

## 14. Keamanan

### Wajib di Production

- [ ] Ganti `SECRET_KEY` dengan nilai acak (`openssl rand -hex 32`)
- [ ] Ganti `DB_PASSWORD` default
- [ ] Set `DEBUG=false`
- [ ] Jangan expose port PostgreSQL (15487) dan Redis (16721) ke internet
- [ ] Gunakan HTTPS via reverse proxy
- [ ] Private key wallet via secret manager, **bukan** file `.env` yang di-commit
- [ ] Set `TRADING_MODE=PAPER` sampai validasi selesai

### File yang Tidak Boleh di-Commit

```
.env
.env.production
.env.local
backups/
*.dump
*.rdb
```

---

## 15. Checklist Deployment

### Pre-Deploy

- [ ] Docker & Docker Compose terinstall
- [ ] Port availability dicek
- [ ] `.env.production` dikonfigurasi
- [ ] `SECRET_KEY` dan `DB_PASSWORD` diganti
- [ ] `package-lock.json` ada di folder frontend
- [ ] Backup database existing (jika update)

### Deploy

- [ ] `docker compose -f docker-compose.prod.yml build`
- [ ] `docker compose -f docker-compose.prod.yml up -d postgres redis`
- [ ] Tunggu postgres & redis healthy
- [ ] `alembic upgrade head`
- [ ] `docker compose -f docker-compose.prod.yml up -d`
- [ ] Verifikasi semua container running/healthy

### Post-Deploy

- [ ] `GET /api/health` → OK
- [ ] Frontend accessible
- [ ] WebSocket connected
- [ ] Worker logs menunjukkan cron jobs berjalan
- [ ] Backup otomatis dijadwalkan
- [ ] Monitoring/alerting dikonfigurasi

---

## Referensi

| Dokumen | Isi |
|---------|-----|
| [deployment.md](deployment.md) | Arsitektur deployment & scaling strategy |
| [security.md](security.md) | Authentication, RBAC, input validation |
| [wallet-security.md](wallet-security.md) | Manajemen private key |
| [observability.md](observability.md) | Logging & metrics |
| [realtime.md](realtime.md) | WebSocket & Redis Pub/Sub |

---

## Quick Reference — Perintah Penting

```bash
# === DEVELOPMENT ===
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose logs -f
docker compose down

# === PRODUCTION ===
docker compose -f docker-compose.prod.yml --env-file .env.production build
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml logs -f --tail=100
docker compose -f docker-compose.prod.yml down

# === MAINTENANCE ===
docker compose restart <service>
docker compose exec postgres psql -U memex -d memex
docker compose exec redis redis-cli
docker stats
docker system df
```
