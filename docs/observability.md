# MemeX — Observability & Monitoring

> Dokumen ini menjelaskan strategi observabilitas untuk memantau kesehatan sistem, performa bot, dan error logging.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Logging Strategy](#2-logging-strategy)
- [3. Metrics Collection](#3-metrics-collection)
- [4. Alerting System](#4-alerting-system)
- [5. System Dashboard](#5-system-dashboard)

---

## 1. Overview

Mengingat MemeX beroperasi secara otonom dalam environment finansial yang sangat cepat, observabilitas adalah kunci. Sistem harus dapat menjawab:
- Apakah scanner sedang berjalan normal?
- Kenapa order ini gagal?
- Berapa latency eksekusi trade?

---

## 2. Logging Strategy

Semua log di-output dalam format **JSON** agar mudah di-ingest oleh log aggregator (misal: ELK Stack, Grafana Loki, atau Datadog).

### 2.1. Log Levels
- **DEBUG:** Detail kalkulasi fitur, probabilitas tiap iterasi model. (Di-disable di production).
- **INFO:** Lifecycle worker (started/stopped), token baru ditemukan, order berhasil dieksekusi.
- **WARNING:** API rate limit terhampiri, slippage adjustment, RPC timeout (dan di-retry).
- **ERROR:** Transaksi gagal secara fatal, database connection error, kill switch diaktifkan.

### 2.2. Contextual Logging
Setiap log entry harus memiliki context:
- `trace_id` (untuk melacak flow dari discovery hingga execution)
- `pair_id`
- `worker_name`

---

## 3. Metrics Collection

Menggunakan Prometheus (via exporter di FastAPI dan ARQ workers) untuk mengumpulkan metrics time-series:

### 3.1. Business Metrics
- Total active positions
- Win rate 24h
- Total PnL 24h
- Token scanned per minute

### 3.2. Technical Metrics
- DEX Screener API response time.
- Blockchain RPC latency.
- Worker queue length (seberapa banyak tugas analisis yang menumpuk).
- Prediction engine inference time (harus < 50ms).
- Database query execution time.

---

## 4. Alerting System

Alert dikirimkan secara realtime ke channel komunikasi operator (seperti Telegram, Discord, atau Slack).

### 4.1. Critical Alerts (Paging)
Memicu notifikasi prioritas tinggi:
- `EMERGENCY_STOP_TRIGGERED`: Kill switch aktif.
- `WALLET_LOW_BALANCE`: Saldo gas fee hampir habis.
- `CONSECUTIVE_TRADE_FAILURES`: 3x transaksi gagal berturut-turut.
- `DATA_SOURCE_DOWN`: DEX Screener tidak merespons selama > 1 menit.

### 4.2. Info / Summary Alerts
Memicu notifikasi senyap (tanpa paging):
- Laporan Daily PnL.
- Posisi baru berhasil dibuka.
- Posisi ditutup karena Take Profit / Stop Loss.

---

## 5. System Dashboard

Selain Web Dashboard yang berisi performa trading, sistem infrastruktur akan dipantau menggunakan **Grafana**.

Panel wajib di Grafana:
- **Worker Health:** Status up/down tiap worker (Discovery, Feature, Risk, Predict, Signal, Execution).
- **RPC Health:** Latency ke node blockchain.
- **Queue Backlog:** Jumlah tugas yang belum diproses di Redis.
- **Error Rate:** Persentase log `ERROR` vs `INFO`.
