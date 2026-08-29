# MemeX — Paper Trading System

> Dokumen ini menjelaskan mode Paper Trading, sebuah sistem untuk menjalankan bot di lingkungan produksi (live market) tanpa mempertaruhkan modal sungguhan.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. How it Works](#2-how-it-works)
- [3. Real vs Paper Data Flow](#3-real-vs-paper-data-flow)
- [4. Implementation Details](#4-implementation-details)
- [5. Transition to Live Trading](#5-transition-to-live-trading)

---

## 1. Overview

Paper Trading (atau Forward Testing) adalah langkah validasi akhir setelah Backtesting. Backtesting menggunakan data masa lalu, sedangkan Paper Trading menggunakan data **masa kini (live)** secara realtime, namun transaksinya hanya dicatat di database (virtual balance), tidak di-broadcast ke blockchain.

**Mengapa ini wajib?**
- Membuktikan bahwa latency sistem, delay network, dan koneksi API DEX Screener tidak merusak strategi.
- Memastikan sistem bekerja dengan baik 24/7 sebelum menghubungkan wallet sungguhan.

---

## 2. How it Works

Ketika user/bot mengaktifkan mode `PAPER`:
1. Sistem akan mengalokasikan saldo virtual (misalnya 10,000 USD virtual).
2. Bot berjalan secara normal: Discovery → Risk Engine → Prediction → Strategy.
3. Saat Signal `BUY` muncul, Strategy Engine mengirim order ke Execution Engine dengan flag `mode: PAPER`.
4. Execution Engine **TIDAK** memanggil Blockchain Adapter (RPC). Sebagai gantinya, ia langsung me-record `Trade` di tabel `positions` dengan harga market saat ini (dikurangi perkiraan slippage).
5. Sistem Monitoring terus melacak pergerakan harga aset. Saat menyentuh Take Profit / Stop Loss, posisi virtual ditutup.

---

## 3. Real vs Paper Data Flow

```text
SIGNAL GENERATED (e.g. BUY)
         |
    Check Mode
    /        \
[LIVE]      [PAPER]
  |            |
Call RPC   Skip RPC
  |            |
Sign Tx    Virtual Execution
  |            |
Confirm    Apply Virtual Slippage
  |            |
Save DB    Save DB (mode='PAPER')
```

---

## 4. Implementation Details

- **Virtual Slippage & Fees:** Sama seperti backtesting, paper trading harus mensimulasikan fee (0.3%) dan network fee agar PnL mencerminkan kondisi real. Jika tidak, paper trading akan terlihat sangat profitable namun hancur di live market.
- **Liquidity Checks:** Walau virtual, jika order $500 dikirim ke koin dengan likuiditas hanya $1000, execution logic harus membatalkan atau mensimulasikan partial fill/extreme slippage.
- **Database Tracking:** Tabel `orders`, `positions`, dan `trades` memiliki kolom `mode` (PAPER / LIVE). Web dashboard memungkinkan user melakukan *toggle* view untuk melihat performa paper account vs live account secara terpisah.

---

## 5. Transition to Live Trading

Transisi dari Paper ke Live sangat mudah, karena seluruh pipeline analisis (`scanner -> risk -> prediction -> strategy`) tidak mengetahui apakah ini paper atau live. Mereka hanya menghasilkan sinyal.

Hanya **Execution Engine** yang membedakan perlakuan berdasarkan flag mode.

Untuk pindah ke Live:
1. User memastikan wallet terkonfigurasi.
2. User mengaktifkan toggle "Live Trading" di dashboard.
3. Config diupdate, sinyal berikutnya akan diarahkan ke Blockchain Adapter.
