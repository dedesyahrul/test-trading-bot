# MemeX — Wallet Security Architecture

> Dokumen ini menjelaskan bagaimana MemeX mengamankan private keys dan dana pengguna di dalam environment cloud/server.

---

## Table of Contents

- [1. Core Principles](#1-core-principles)
- [2. Threat Model](#2-threat-model)
- [3. Key Management Architecture](#3-key-management-architecture)
- [4. Operational Limits](#4-operational-limits)
- [5. Emergency Protocols (Kill Switch)](#5-emergency-protocols-kill-switch)

---

## 1. Core Principles

Manajemen private key adalah bagian paling berisiko dari automated trading bot.
Prinsip utama MemeX:
1. **Never persist plaintext keys:** Private key **TIDAK PERNAH** disimpan di dalam database PostgreSQL dalam bentuk plaintext.
2. **In-memory only:** Private key hanya di-load ke dalam RAM saat aplikasi (Worker) *boot up*.
3. **Principle of Least Privilege:** Hanya `ExecutionWorker` yang memiliki akses ke modul penandatanganan transaksi. Web API, Discovery Worker, dan ML Worker tidak memiliki akses.

---

## 2. Threat Model

Sistem dirancang untuk memitigasi serangan berikut:
- **Database Dump/Leak:** Hacker membobol database PostgreSQL. (Mitigasi: DB tidak menyimpan private key, hanya public address).
- **Source Code Leak:** Source code bocor ke publik. (Mitigasi: Code tidak mengandung hardcoded secret).
- **Server File System Access (Partial):** Hacker mendapatkan akses read ke filesystem. (Mitigasi: Private key tidak disimpan dalam plain text `.env` jika memungkinkan, atau dienkripsi).

---

## 3. Key Management Architecture

Terdapat dua pendekatan yang didukung oleh MemeX, tergantung pada level infrastruktur:

### Level 1: Encrypted Environment Variables (Minimum)
Cocok untuk self-hosting/VPS.
1. Private key disimpan dalam file `.env.secrets`.
2. File ini di-encrypt menggunakan SOPS atau sekadar di-set read-only hanya untuk user spesifik (`chmod 400`).
3. Saat docker container dijalankan, secret di-inject sebagai environment variables.

### Level 2: External Secret Manager (Recommended)
Cocok untuk cloud deployment (AWS/GCP).
1. Menggunakan HashiCorp Vault, AWS Secrets Manager, atau GCP Secret Manager.
2. Worker saat startup melakukan autentikasi via IAM Role.
3. Worker menarik private key dari Secret Manager langsung ke RAM.

---

## 4. Operational Limits

Untuk mengurangi dampak eksploitasi jika (worst case) bot *goes rogue* akibat bug pada logic:

1. **Trade Size Limit:** Hardcoded limit maksimum per trade (misal 5 SOL / $1000). Order yang melebihi ini akan di-reject di level Execution Engine.
2. **Daily Loss Limit:** Jika total kerugian pada hari berjalan melebihi persentase tertentu (misal 10% dari modal), trading akan otomatis berhenti selama 24 jam.
3. **Withdrawal Protection:** Bot didesain **hanya** untuk melakukan fungsi swap/trade di DEX yang di-whitelist. Bot **TIDAK** memiliki modul/logic untuk mentransfer saldo (send token) ke wallet lain.

---

## 5. Emergency Protocols (Kill Switch)

Admin Dashboard memiliki tombol **"EMERGENCY STOP" (Kill Switch)**.

Jika Kill Switch diaktifkan (disimpan di Redis untuk read instan):
1. Sistem men-set flag `EMERGENCY_STOP = TRUE`.
2. Semua `BUY` signals baru akan ditolak.
3. Semua order yang masih *pending* di queue akan dibatalkan.
4. (Opsional/Configurable) Bot akan berusaha mengeksekusi "Market Sell" pada seluruh posisi terbuka (*liquidate all*) untuk mengembalikan dana menjadi native token / stablecoin.
5. Bot mematikan modul koneksi RPC hingga dihidupkan manual oleh admin.
