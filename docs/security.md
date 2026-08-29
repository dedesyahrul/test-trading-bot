# MemeX — System Security

> Dokumen ini menjelaskan keamanan sistem di tingkat aplikasi, API, dan akses pengguna. Untuk keamanan wallet, lihat [wallet-security.md](wallet-security.md).

---

## Table of Contents

- [1. Authentication & Authorization](#1-authentication--authorization)
- [2. API Security](#2-api-security)
- [3. Application Security](#3-application-security)
- [4. Database Security](#4-database-security)
- [5. Audit Trail](#5-audit-trail)

---

## 1. Authentication & Authorization

MemeX didesain sebagai platform yang digunakan oleh *operator/admin*, bukan public SaaS.

### 1.1. JWT Authentication
- Semua API endpoints (kecuali `/health`) dilindungi oleh JWT (JSON Web Tokens).
- Access Token memiliki umur pendek (misal: 15 menit).
- Refresh Token digunakan untuk mendapatkan access token baru, disimpan secara aman (HttpOnly cookies).

### 1.2. Role-Based Access Control (RBAC)
- **Admin:** Memiliki full access (start/stop bot, ubah parameter risk, manual override).
- **Viewer:** Hanya dapat melihat dashboard (balance, PnL, posisi terbuka), tidak dapat mengubah konfigurasi.

---

## 2. API Security

1. **CORS (Cross-Origin Resource Sharing):** Dikonfigurasi secara strict hanya mengizinkan domain frontend yang telah ditentukan.
2. **Rate Limiting:** Diterapkan di level reverse proxy (Nginx/Traefik) dan di level aplikasi (FastAPI `slowapi`) untuk mencegah brute-force login.
3. **Input Validation:** Semua input payload divalidasi secara ketat menggunakan Pydantic models. Data yang tidak sesuai tipe atau format akan ditolak sebelum menyentuh logic bisnis.

---

## 3. Application Security

1. **Dependency Scanning:** Menggunakan tools (seperti `safety` untuk Python) dalam CI/CD pipeline untuk mendeteksi dependency library yang memiliki CVE (Common Vulnerabilities and Exposures).
2. **No Eval/Exec:** Aplikasi sama sekali tidak menggunakan fungsi evaluasi kode dinamis untuk menghindari Remote Code Execution (RCE).
3. **Error Handling:** Environment production (`NODE_ENV=production` atau `APP_ENV=prod`) akan menyembunyikan stack trace dari client.

---

## 4. Database Security

1. **Network Isolation:** PostgreSQL dan Redis tidak di-expose ke internet publik. Mereka hanya dapat diakses melalui private network (Docker bridge network / VPC).
2. **Parameterized Queries:** SQLAlchemy ORM / Query Builder secara otomatis menggunakan parameterized queries untuk mencegah SQL Injection.
3. **Password Hashing:** Password pengguna di-hash menggunakan algoritma modern dan kuat (Bcrypt / Argon2id).

---

## 5. Audit Trail

Segala bentuk interaksi yang mengubah state sistem dicatat di dalam tabel `audit_logs`.

Event yang diaudit meliputi:
- User login / logout (termasuk failed attempts).
- Perubahan parameter trading (misal: mengganti max slippage dari 5% ke 10%).
- Pengaktifan atau penonaktifan Kill Switch.
- Intervensi manual pada order/posisi.

Log ini bersifat *append-only* dan dirancang untuk keperluan forensik apabila terjadi anomali sistem.
