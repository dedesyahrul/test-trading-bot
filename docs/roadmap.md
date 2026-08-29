# MemeX — Development Roadmap

> Dokumen ini merangkum fase pengembangan platform dari konsepsi hingga produksi.

---

## Table of Contents

- [Phase 0: Design & Architecture (Current)](#phase-0-design--architecture-current)
- [Phase 1: Foundation & Data Pipeline](#phase-1-foundation--data-pipeline)
- [Phase 2: Intelligence & Backtesting](#phase-2-intelligence--backtesting)
- [Phase 3: Execution & Paper Trading](#phase-3-execution--paper-trading)
- [Phase 4: Dashboard & Production Readiness](#phase-4-dashboard--production-readiness)

---

## Phase 0: Design & Architecture (Current)

_Target: System Blueprint_

- [x] Mendefinisikan Requirements.
- [x] Mendesain Arsitektur.
- [x] Mendokumentasikan System (Semua file markdown di folder `docs/`).
- [x] Review akhir oleh tim/owner.

---

## Phase 1: Foundation & Data Pipeline

_Target: Dapat membaca data dari DEX Screener dan menyimpannya ke Database._

1. **Setup Project:** Inisialisasi FastAPI, SQLAlchemy, Alembic, Docker Compose.
2. **Database Migration:** Menerjemahkan `database.md` menjadi tabel PostgreSQL.
3. **Worker Infrastructure:** Setup ARQ dan Redis.
4. **API Integration:** Membuat `Collector` untuk memanggil endpoint DEX Screener secara periodik.
5. **Data Ingestion:** Menyimpan `market_snapshots` dan token baru ke database tanpa terblokir rate limit.

---

## Phase 2: Intelligence & Backtesting

_Target: Sistem dapat mengenali peluang dan mengujinya pada data historis._

1. **Feature Engineering:** Membuat pipeline untuk menghitung momentum, volume spike, dan liquidity ratio dari data historis di DB.
2. **Risk Engine:** Mengimplementasikan logic hard constraints dan risk scoring.
3. **ML Pipeline:** Menyiapkan script untuk melatih model LightGBM secara offline menggunakan dataset lokal.
4. **Strategy Engine:** Membuat kerangka _BaseStrategy_ dan mengimplementasikan _MomentumStrategy_.
5. **Backtesting System:** Membuat engine simulasi untuk mem-backtest strategi dan melihat metrik performa.

---

## Phase 3: Execution & Paper Trading

_Target: Sistem beroperasi secara live, namun dengan dana virtual (Paper Trading)._

1. **Blockchain Abstraction:** Menulis adapter untuk integrasi blockchain (Solana / EVM).
2. **Execution Worker:** Mengembangkan logic penandatanganan transaksi dan validasi slippage (hanya level kode/struktur).
3. **Paper Trading Mode:** Menghubungkan Strategy Engine ke Execution Engine dalam mode `PAPER`.
4. **Live Monitoring:** Membiarkan bot berjalan selama 7 hari penuh di Paper Trading Mode dan menganalisis PnL serta kestabilan sistem.

---

## Phase 4: Dashboard & Production Readiness

_Target: UI untuk kontrol dan peluncuran menggunakan modal sesungguhnya._

1. **REST API:** Membangun endpoint untuk dashboard.
2. **WebSocket Server:** Mengatur sinkronisasi event real-time (Redis Pub/Sub -> WebSocket).
3. **Vue.js Frontend:** Membangun dashboard utama, kontrol strategi, dan kill switch.
4. **Security Audit:** Meninjau manajemen private key, env vars, dan konfigurasi jaringan.
5. **Live Trading Launch:** Migrasi mode dari `PAPER` ke `LIVE` dengan modal uji coba yang kecil.
