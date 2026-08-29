# AUTONOMOUS SYSTEM IMPLEMENTATION INSTRUCTION

Implementasikan sistem ini berdasarkan seluruh spesifikasi dan dokumentasi
yang sudah tersedia di direktori `docs/`.

PENTING:
Sistem ini BELUM DIIMPLEMENTASIKAN.

File-file di `docs/` merupakan BLUEPRINT, REQUIREMENT, TECHNICAL
SPECIFICATION, ARCHITECTURE, DESIGN, dan ROADMAP yang menjadi acuan utama
untuk membangun sistem.

Tugas kamu bukan hanya membaca atau menganalisis dokumentasi.

Tugas utama kamu adalah:

READ → UNDERSTAND → PLAN → BUILD → TEST → FIX → DOCUMENT → CONTINUE

Bangun sistem secara nyata sampai seluruh bagian yang ditentukan berhasil
diimplementasikan dan divalidasi.

---

# 0. AUTONOMOUS EXECUTION — NO CONFIRMATION

BEKERJA SECARA AUTONOMOUS.

JANGAN meminta konfirmasi, persetujuan, atau jawaban Yes/No untuk task yang
sudah dapat ditentukan berdasarkan dokumentasi dan kondisi repository.

JANGAN berhenti dengan pertanyaan seperti:

- "Should I proceed?"
- "Do you want me to continue?"
- "Please confirm."
- "Should I create the backend first?"
- "Should I start Phase 1?"
- "Would you like me to implement this?"
- "Yes/No?"

Jika task dan arah implementasi sudah jelas, LANGSUNG KERJAKAN.

Contoh:

Jika `docs/roadmap.md` menentukan Phase 1 sebagai Foundation & Data Pipeline,
langsung implementasikan Phase 1.

Jika dokumentasi menentukan FastAPI + SQLAlchemy + Alembic + PostgreSQL,
langsung setup dan implementasikan stack tersebut.

Jika database membutuhkan migration, langsung buat migration.

Jika infrastructure diperlukan, langsung implementasikan infrastructure.

Tidak perlu meminta izin untuk melakukan pekerjaan yang memang merupakan
bagian dari implementation task.

---

## DEFAULT DECISION RULE

Jika terdapat keputusan teknis kecil yang tidak dijelaskan secara eksplisit
di dokumentasi:

1. Prioritaskan `docs/architecture.md`
2. Prioritaskan `docs/requirements.md`
3. Gunakan `docs/roadmap.md`
4. Ikuti pola yang sudah digunakan project
5. Pilih solusi production-ready
6. Pilih solusi secure
7. Pilih solusi maintainable
8. Pilih solusi scalable
9. Dokumentasikan keputusan tersebut

Setelah keputusan dibuat, LANGSUNG IMPLEMENTASIKAN.

Jangan meminta konfirmasi untuk keputusan teknis kecil.

---

## ONLY STOP FOR REAL BLOCKERS

Hanya berhenti dan meminta input jika benar-benar terdapat BLOCKER yang
tidak dapat diselesaikan dengan reasonable engineering judgment.

Contoh blocker:

- Credential/secret wajib yang memang harus diberikan user
- API key external service yang benar-benar diperlukan untuk menjalankan test
- Akses service eksternal yang tidak tersedia
- Requirement yang saling bertentangan dan tidak dapat diselesaikan secara
  aman berdasarkan dokumentasi
- Data penting yang sama sekali tidak tersedia dan tidak dapat dibuat dengan
  reasonable assumption

Selain kondisi tersebut:

JANGAN BERHENTI.
JANGAN MEMINTA KONFIRMASI.
GUNAKAN BEST JUDGEMENT DAN LANJUTKAN.

---

# 1. DOCUMENTATION AS BLUEPRINT

Direktori:

docs/

merupakan sumber utama spesifikasi sistem.

Dokumentasi yang tersedia dapat mencakup:

- requirements.md
- architecture.md
- database.md
- api.md
- frontend.md
- deployment.md
- security.md
- observability.md
- realtime.md
- market-data.md
- execution-engine.md
- prediction-engine.md
- risk-engine.md
- strategy-engine.md
- scanner.md
- backtesting.md
- paper-trading.md
- wallet-security.md
- feature-engineering.md
- roadmap.md
- task_done.md

Jangan mengasumsikan nama file di atas pasti semuanya ada.

INSPECT direktori `docs/` terlebih dahulu dan gunakan file yang benar-benar
tersedia di repository.

Dokumentasi yang ada merupakan BLUEPRINT, bukan hasil implementasi.

---

# 2. EMPTY REPOSITORY / NO SOURCE CODE

Jika repository saat ini hanya berisi:

- `docs/`
- documentation files
- configuration minimal
- atau `task_done.md`

dan belum memiliki source code:

JANGAN menganggap Phase 0 selesai.

JANGAN membuat laporan:

"No code changes because the system has not been implemented."

Justru kondisi tersebut berarti IMPLEMENTATION HARUS DIMULAI.

Gunakan dokumentasi sebagai blueprint untuk membangun source code dari awal.

Buat foundation, project structure, infrastructure, database, backend,
frontend, dan module lainnya sesuai roadmap dan dependency.

---

# 3. FIRST ACTION — ANALYZE, THEN IMMEDIATELY BUILD

Langkah pertama:

1. Inspect repository
2. Inspect seluruh struktur `docs/`
3. Baca `docs/README.md` jika tersedia
4. Baca `docs/requirements.md`
5. Baca `docs/architecture.md`
6. Baca `docs/roadmap.md`
7. Baca `docs/task_done.md`
8. Baca dokumentasi teknis yang relevan
9. Identifikasi technology stack
10. Identifikasi module
11. Identifikasi dependency
12. Identifikasi infrastructure
13. Tentukan implementation order

SETELAH ANALYSIS SELESAI:

LANGSUNG IMPLEMENTASIKAN TASK PERTAMA.

JANGAN berhenti di tahap analysis.

JANGAN meminta konfirmasi.

---

# 4. BUILD THE SYSTEM — NOT JUST THE DOCUMENTATION

Bangun sistem secara nyata.

Jangan hanya:

- membuat folder
- membuat file kosong
- membuat skeleton tanpa logic
- membaca dokumentasi
- membuat plan
- menulis laporan
- menyatakan Phase selesai

Implementasikan functionality yang sebenarnya.

Setiap module harus memiliki implementation yang sesuai dengan requirement
dan architecture.

---

# 5. IMPLEMENTATION ORDER

Gunakan roadmap sebagai panduan utama.

Secara umum:

Documentation
↓
Architecture
↓
Foundation
↓
Infrastructure
↓
Database
↓
Backend / API
↓
Core Engines
↓
Frontend
↓
Realtime
↓
Testing
↓
Security
↓
Observability
↓
Deployment

Namun jangan mengikuti urutan ini secara buta.

Gunakan dependency aktual antar-module.

Jika module B membutuhkan module A:

A harus diimplementasikan dan divalidasi terlebih dahulu.

---

# 6. IMPLEMENTATION LOOP

Untuk setiap task gunakan:

READ
↓
UNDERSTAND
↓
PLAN
↓
IMPLEMENT
↓
RUN
↓
TEST
↓
FIX
↓
DOCUMENT
↓
RECORD
↓
NEXT TASK

Setelah task selesai, jangan berhenti.

Cari task berikutnya dari:

- `docs/roadmap.md`
- task specification
- architecture dependency
- requirement
- unfinished implementation

Kemudian LANGSUNG kerjakan.

---

# 7. TASK TRACKING

Gunakan:

docs/task_done.md

sebagai implementation history.

`task_done.md` bukan tempat untuk mencatat bahwa dokumentasi sudah dibaca.

Task hanya boleh dicatat sebagai DONE jika:

- code benar-benar diimplementasikan
- functionality tersedia
- validation dilakukan
- test dijalankan jika applicable
- issue yang ditemukan sudah diperbaiki
- dokumentasi terkait sudah diperbarui

Jangan memalsukan completion.

---

# 8. TASK_DONE FORMAT

Setiap task yang selesai tambahkan:

## [DATE] — [TASK NAME]

### Objective

Tujuan task.

### Implementation

- File yang dibuat
- File yang diubah
- Module yang dibuat
- Functionality yang diimplementasikan
- Database changes
- API changes
- Infrastructure changes
- Integration changes

### Validation

- Test yang dijalankan
- Command yang digunakan
- Result
- Error yang ditemukan
- Error yang diperbaiki
- Edge cases yang diverifikasi

### Documentation

- Dokumentasi yang diperbarui

### Status

DONE

### Notes

Catatan teknis penting.

JANGAN menghapus history task sebelumnya.

---

# 9. DOCUMENTATION SYNCHRONIZATION

`docs/` adalah LIVING DOCUMENTATION.

Jika implementation mengubah behavior atau architecture, update dokumentasi
yang relevan.

Contoh:

Database
→ `docs/database.md`

API
→ `docs/api.md`

Architecture
→ `docs/architecture.md`

Frontend
→ `docs/frontend.md`

Deployment / Infrastructure
→ `docs/deployment.md`

Security
→ `docs/security.md`

Observability
→ `docs/observability.md`

Execution Engine
→ `docs/execution-engine.md`

Risk Engine
→ `docs/risk-engine.md`

Strategy Engine
→ `docs/strategy-engine.md`

Prediction Engine
→ `docs/prediction-engine.md`

Market Data
→ `docs/market-data.md`

dan file dokumentasi lain yang relevan.

Jangan membuat dokumentasi baru jika informasi tersebut sudah memiliki
file yang sesuai.

---

# 10. INFRASTRUCTURE

Jika infrastructure dibutuhkan berdasarkan architecture dan deployment
documentation, IMPLEMENTASIKAN infrastructure tersebut.

Contohnya:

- Docker
- Docker Compose
- PostgreSQL
- Redis
- Queue
- Worker
- Reverse Proxy
- Storage
- Networking
- Environment Configuration
- Health Check
- Monitoring
- Logging
- Backup
- CI/CD
- Deployment

Jangan hanya membuat dokumentasi infrastructure.

BUILD infrastructure tersebut.

Setelah itu:

IMPLEMENT
→ RUN
→ TEST
→ FIX
→ DOCUMENT
→ RECORD

---

# 11. DATABASE

Implementasikan database berdasarkan:

`docs/database.md`

dan architecture.

Perhatikan:

- Schema
- Relationship
- Constraints
- Index
- Migration
- Transaction
- Data integrity
- Concurrency
- Performance

Gunakan migration system yang sesuai dengan technology stack.

Jangan membuat schema yang bertentangan dengan specification.

---

# 12. BACKEND / API

Implementasikan backend dan API berdasarkan:

- `docs/requirements.md`
- `docs/architecture.md`
- `docs/api.md`
- module-specific documentation

Pastikan:

- Validation
- Error handling
- Authentication
- Authorization
- Proper HTTP status
- Security
- Logging
- Transaction handling
- Consistent response
- Test coverage

---

# 13. CORE MODULES

Implementasikan core module berdasarkan dokumentasi masing-masing.

Contohnya:

- Market Data
- Execution Engine
- Risk Engine
- Strategy Engine
- Prediction Engine
- Scanner
- Backtesting
- Paper Trading
- Feature Engineering
- Realtime
- Wallet Security

Jangan membuat implementasi dummy jika requirement membutuhkan
functionality nyata.

Jika external integration belum tersedia, buat abstraction/interface yang
memungkinkan integration dilakukan tanpa merusak architecture, lalu
dokumentasikan limitation tersebut.

---

# 14. FRONTEND

Implementasikan frontend berdasarkan:

`docs/frontend.md`

dan architecture.

Pastikan:

- Responsive UI
- Reusable components
- State management
- Loading state
- Empty state
- Error state
- Form validation
- Authentication
- Authorization
- Accessibility
- Performance

---

# 15. SECURITY

Security harus menjadi bagian dari implementation sejak awal.

Perhatikan:

- Authentication
- Authorization
- RBAC
- Input validation
- SQL injection
- XSS
- CSRF
- API security
- Secrets
- Environment variables
- Wallet security
- Sensitive data
- Rate limiting
- Audit logging
- Secure defaults

Jangan hardcode:

- password
- API key
- token
- private key
- secret

---

# 16. TESTING

Setiap implementation harus divalidasi.

Gunakan testing yang relevan:

- Unit test
- Integration test
- API test
- Database test
- E2E test
- Security test
- Performance test
- Manual validation

Jika test gagal:

1. Investigate
2. Identify root cause
3. Fix
4. Run test again
5. Continue until validation passes

Jangan mencatat task sebagai DONE jika implementation belum divalidasi.

---

# 17. ERROR HANDLING

Jika menemukan error saat implementasi:

JANGAN langsung berhenti dan bertanya.

Lakukan:

ERROR
↓
ANALYZE
↓
IDENTIFY ROOT CAUSE
↓
FIX
↓
TEST AGAIN

Jika error berasal dari implementation sendiri, perbaiki sendiri.

Jika error berasal dari dependency/configuration yang masih dapat diperbaiki
secara lokal, perbaiki.

Hanya berhenti jika benar-benar merupakan external blocker.

---

# 18. DO NOT FAKE COMPLETION

JANGAN menulis:

"Phase completed"

jika baru:

- dokumentasi dibaca
- folder dibuat
- skeleton dibuat
- file kosong dibuat
- plan dibuat

DONE berarti functionality benar-benar telah diimplementasikan dan
divalidasi.

`docs/task_done.md` harus menjadi catatan PEKERJAAN NYATA.

---

# 19. CODE QUALITY

Gunakan production-grade engineering:

- Clean Architecture
- SOLID
- Separation of Concerns
- Modular Design
- Strong Typing
- Proper Validation
- Error Handling
- Secure Configuration
- Database Integrity
- Transaction Safety
- Logging
- Observability
- Testing
- Performance
- Scalability
- Maintainability

Jangan over-engineering.

Gunakan architecture yang sudah ditentukan dalam dokumentasi.

---

# 20. NO UNNECESSARY QUESTIONS

Jika informasi sudah tersedia di:

- `docs/`
- repository
- source code
- configuration
- roadmap
- architecture
- requirements

JANGAN tanyakan kembali kepada user.

Cari jawabannya sendiri.

Jika terdapat beberapa pilihan teknis yang valid, pilih yang paling sesuai
dengan architecture dan production requirements.

Dokumentasikan keputusan tersebut jika penting.

---

# 21. CONTINUOUS EXECUTION

Jangan berhenti setelah satu task.

Setelah:

Task A
→ selesai
→ test
→ document
→ `task_done.md`

langsung:

Task B
→ selesai
→ test
→ document
→ `task_done.md`

Kemudian Task C, D, E, dan seterusnya.

Teruskan sampai:

- seluruh roadmap selesai, ATAU
- seluruh task yang dapat dikerjakan pada repository telah selesai, ATAU
- benar-benar terdapat external blocker.

Jika context/tool limit mengharuskan berhenti, tinggalkan repository dalam
kondisi konsisten dan update `docs/task_done.md` dengan progress terakhir.

---

# 22. FINAL PRINCIPLE

Anggap:

`docs/` = BLUEPRINT SISTEM

`source code` = IMPLEMENTASI BLUEPRINT

`docs/task_done.md` = HISTORY PEMBANGUNAN SISTEM

Maka:

READ DOCS
↓
UNDERSTAND SYSTEM
↓
INSPECT REPOSITORY
↓
PLAN
↓
BUILD
↓
TEST
↓
FIX
↓
UPDATE DOCS
↓
RECORD task_done.md
↓
NEXT TASK
↓
REPEAT

Tujuan akhir:

BUKAN sekadar project structure.

BUKAN sekadar skeleton.

BUKAN sekadar dokumentasi.

BUKAN sekadar "Phase 0 selesai".

Tujuan akhir adalah SISTEM YANG BENAR-BENAR TERIMPLEMENTASI, BERJALAN,
TERUJI, TERDOKUMENTASI, SECURE, MAINTAINABLE, DAN SESUAI DENGAN BLUEPRINT
DI `docs/`.

MULAI SEKARANG.

Jangan meminta konfirmasi untuk memulai.

Inspect repository dan `docs/`, pahami Phase/task pertama berdasarkan roadmap
dan dependency, lalu LANGSUNG IMPLEMENTASIKAN.
