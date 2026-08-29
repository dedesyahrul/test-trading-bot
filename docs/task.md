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

# 23. RESUME / RECOVERY / CONTINUATION

Sistem harus dapat dilanjutkan kapan saja tanpa kehilangan konteks pekerjaan.

Pekerjaan dapat terhenti karena:

- Internet terputus
- Session berakhir
- Context limit
- Tool error
- Computer restart
- Agent dihentikan
- User melanjutkan project di hari berikutnya

Jika execution dimulai kembali, JANGAN langsung mengerjakan task dari awal.

Selalu lakukan RECOVERY ANALYSIS terlebih dahulu.

---

## 23.1 RECOVERY ANALYSIS — FIRST ACTION

Setiap kali agent mulai bekerja pada repository yang sudah pernah dikerjakan,
LANGKAH PERTAMA WAJIB adalah melakukan state analysis.

Jangan langsung coding.

Gunakan urutan:

1. Inspect current repository
2. Inspect `docs/`
3. Read `docs/task_done.md`
4. Read `docs/roadmap.md`
5. Read relevant documentation
6. Inspect source code yang sudah ada
7. Inspect database/migrations jika tersedia
8. Inspect configuration/infrastructure
9. Check git status jika repository menggunakan Git
10. Run relevant tests / health checks
11. Compare documented progress dengan kondisi repository aktual
12. Identify completed task
13. Identify partially completed task
14. Identify failed task
15. Identify pending task
16. Identify broken/inconsistent implementation
17. Determine the NEXT TASK

Setelah recovery analysis selesai:

LANGSUNG LANJUTKAN DARI STATE TERAKHIR.

JANGAN meminta konfirmasi.

---

# 24. DETERMINE CURRENT PROJECT STATE

Jangan hanya mempercayai `docs/task_done.md`.

`docs/task_done.md` adalah implementation history,
tetapi kondisi repository aktual adalah sumber kebenaran untuk menentukan
apakah implementation benar-benar sudah selesai.

Bandingkan:

Repository

- Source Code
- Tests
- Configuration
- Database/Migrations
- Infrastructure
- `docs/task_done.md`
- `docs/roadmap.md`

Kemudian tentukan:

### COMPLETED

Task sudah benar-benar implemented dan validated.

### IN PROGRESS

Task sudah dimulai tetapi belum selesai.

### PARTIALLY COMPLETED

Sebagian implementation sudah ada tetapi masih terdapat pekerjaan.

### FAILED

Implementation ada tetapi validation/test gagal.

### PENDING

Task belum dimulai.

### BLOCKED

Task tidak dapat dilanjutkan karena external blocker.

---

# 25. NEVER REPEAT COMPLETED WORK

Jika recovery analysis menemukan task:

DONE

dan implementation memang sudah tersedia serta tervalidasi:

JANGAN mengulang implementation tersebut.

Gunakan hasil yang sudah ada dan lanjutkan ke task berikutnya.

Namun jika `task_done.md` mengatakan DONE tetapi repository menunjukkan bahwa
implementation sebenarnya belum lengkap atau test gagal:

JANGAN percaya status DONE secara buta.

Treat task tersebut sebagai:

INCOMPLETE / NEEDS VERIFICATION

Lakukan verification dan perbaiki implementation sebelum melanjutkan.

---

# 26. PARTIAL IMPLEMENTATION RECOVERY

Jika execution terhenti di tengah task, misalnya:

TASK-005 — Execution Engine

sudah membuat:

- interface
- database model
- sebagian service

tetapi belum selesai:

- worker
- integration
- tests

JANGAN mengulang dari awal.

Inspect implementation yang sudah ada.

Tentukan bagian yang sudah benar-benar selesai.

Kemudian lanjutkan dari bagian yang belum selesai.

Jika diperlukan, update `docs/task_done.md` agar status mencerminkan kondisi
aktual.

Gunakan:

IN PROGRESS

atau

PARTIALLY COMPLETED

sampai seluruh task selesai dan tervalidasi.

---

# 27. TASK STATE MUST BE RECOVERABLE

Setiap task yang sedang dikerjakan harus meninggalkan jejak yang cukup agar
agent berikutnya dapat memahami posisi terakhir.

Jika task belum selesai ketika execution berhenti, dokumentasikan progress
terakhir jika memungkinkan.

Gunakan format:

## [DATE] — TASK NAME

### Status

IN PROGRESS

### Completed

- Bagian yang sudah selesai
- File yang sudah dibuat
- Migration yang sudah dibuat
- API yang sudah selesai

### Remaining

- Bagian yang belum selesai
- Test yang belum dilakukan
- Integration yang belum selesai

### Current State

Penjelasan kondisi implementation saat terakhir berhenti.

### Next Action

Apa langkah berikutnya yang harus dilakukan.

---

# 28. STARTUP STATE REPORT

Setiap kali memulai atau melanjutkan pekerjaan, lakukan analisis state terlebih
dahulu.

Sebelum coding, buat internal startup assessment seperti:

PROJECT STATE
─────────────
Documentation : READY
Architecture : READY
Foundation : DONE
Database : DONE
Market Data : DONE
Execution : IN PROGRESS
Risk Engine : PENDING

CURRENT TASK
────────────
TASK-005 — Execution Engine

COMPLETED
─────────

- Interface
- Models
- Repository

REMAINING
─────────

- Service implementation
- Worker
- Integration tests

NEXT ACTION
───────────
Continue Execution Engine service implementation.

Setelah state diketahui, LANGSUNG kerjakan `NEXT ACTION`.

Tidak perlu meminta konfirmasi kepada user.

---

# 29. CROSS-CHECK DOCUMENTATION VS CODE

Jika terdapat perbedaan antara dokumentasi dan repository:

Contoh:

`docs/task_done.md`:
"Database migration completed."

Tetapi repository:
migration belum ada.

Maka jangan menganggap task selesai.

Lakukan verification.

Prioritas untuk menentukan kondisi aktual:

1. Running system
2. Source code
3. Tests
4. Database/migrations
5. Infrastructure
6. Documentation/history

Dokumentasi harus diperbaiki agar mencerminkan kondisi aktual.

---

# 30. GIT / WORKTREE RECOVERY

Jika Git tersedia, gunakan:

- `git status`
- `git diff`
- `git log`
- relevant commit history

untuk memahami perubahan terakhir.

Jangan melakukan destructive operation seperti:

- reset
- checkout -- .
- clean
- force overwrite

yang dapat menghilangkan pekerjaan sebelumnya.

Jaga semua perubahan yang sudah ada.

Jika terdapat uncommitted changes, inspect terlebih dahulu sebelum mengubahnya.

Jangan menghapus pekerjaan yang belum selesai.

---

# 31. INTERRUPTION SAFETY

Jika execution akan berhenti atau tool/context limit hampir tercapai:

Prioritaskan meninggalkan repository dalam kondisi konsisten.

Jika memungkinkan:

1. Finish current atomic operation
2. Run validation
3. Update relevant documentation
4. Update `docs/task_done.md`
5. Mark current state sebagai `IN PROGRESS` jika belum selesai
6. Record remaining work
7. Record next action

Jangan menandai task sebagai DONE jika belum selesai.

---

# 32. NEXT SESSION BEHAVIOR

Ketika user membuka session baru dan mengatakan:

"lanjutkan"

atau:

"lanjutkan project"

atau bahkan hanya menjalankan agent kembali,

JANGAN bertanya:

"Terakhir mengerjakan apa?"

Cari sendiri dari repository.

Lakukan:

RECOVERY ANALYSIS
→ DETERMINE STATE
→ FIND LAST COMPLETED TASK
→ FIND CURRENT IN-PROGRESS TASK
→ VERIFY
→ FIND NEXT TASK
→ IMPLEMENT

Jika tidak ada task IN PROGRESS:

Cari task PENDING pertama berdasarkan dependency dan roadmap.

Jika ada task IN PROGRESS:

Lanjutkan task tersebut.

Jika task IN PROGRESS ternyata sudah selesai tetapi belum dicatat:

Validasi → update documentation → update `task_done.md` → lanjut task berikutnya.

---

# 33. CONTINUOUS PROJECT MEMORY

Jangan mengandalkan memory dari conversation/session sebelumnya.

Repository harus menjadi sumber state yang dapat dipulihkan.

Informasi penting mengenai progress harus tersimpan di:

- source code
- Git
- `docs/task_done.md`
- documentation terkait

Dengan demikian project dapat dilanjutkan walaupun:

- conversation baru
- session baru
- agent baru
- computer restart
- internet terputus
- context sebelumnya hilang

Targetnya:

NEW SESSION
↓
INSPECT REPOSITORY
↓
READ PROJECT STATE
↓
UNDERSTAND LAST PROGRESS
↓
VERIFY
↓
CONTINUE

--

# 34. DOCKER & PORT MANAGEMENT

SEBELUM membuat, menjalankan, atau melakukan rebuild Docker container/service,
WAJIB melakukan pengecekan port terlebih dahulu.

JANGAN langsung menggunakan port default tanpa melakukan pemeriksaan.

## PORT CHECK

Sebelum menjalankan Docker:

1. Inspect semua port yang sedang digunakan oleh host.
2. Inspect port yang digunakan oleh existing Docker containers.
3. Inspect port yang digunakan oleh service lain di repository.
4. Inspect port yang sudah didefinisikan pada configuration/environment.
5. Identifikasi port conflict.
6. Pilih port host yang:
   - belum digunakan
   - tidak conflict dengan Docker
   - tidak conflict dengan service existing
   - tidak conflict dengan configuration project
   - relatif jarang digunakan
   - sesuai dengan kebutuhan service
7. Gunakan port tersebut secara konsisten.

Jangan mengasumsikan port tertentu tersedia.

---

## PORT SELECTION RULE

Prioritaskan penggunaan port non-default yang masih valid dan belum digunakan.

Hindari menggunakan port yang sangat umum jika tidak diperlukan, misalnya:

- 80
- 443
- 3000
- 5000
- 8000
- 8080
- 5432
- 6379

Port di atas tidak dilarang secara mutlak, tetapi JANGAN menggunakannya jika
terdapat alternatif port yang lebih aman dan tidak conflict.

Pilih port yang relatif jarang digunakan dan tersedia pada host.

Contoh:

Jika PostgreSQL biasanya menggunakan `5432`, jangan langsung expose:

5432:5432

Jika `15432` tersedia, dapat gunakan:

15432:5432

Artinya:

HOST PORT : CONTAINER PORT

Gunakan prinsip yang sama untuk service lainnya.

---

## IMPORTANT: CONTAINER PORT VS HOST PORT

Bedakan:

HOST PORT
dan
CONTAINER PORT.

Jangan mengubah container port internal hanya karena host port conflict.

Jika memungkinkan, pertahankan port internal sesuai architecture/image/service
dan ubah hanya host port.

Contoh:

PostgreSQL:

15432:5432

Redis:

16379:6379

Backend:

18000:8000

Frontend:

13000:3000

Angka di atas hanya CONTOH.

Jangan menggunakan contoh tersebut secara otomatis.

SELALU lakukan port availability check terlebih dahulu.

---

## PORT CONSISTENCY

Setelah memilih port:

1. Update `.env` / `.env.example` jika diperlukan.
2. Update Docker Compose.
3. Update configuration yang relevan.
4. Update documentation.
5. Update `docs/deployment.md`.
6. Catat perubahan pada `docs/task_done.md`.

Jangan sampai Docker menggunakan satu port tetapi dokumentasi atau environment
menggunakan port yang berbeda.

---

## PORT CONFLICT RECOVERY

Jika Docker gagal start karena:

"port is already allocated"

atau:

"address already in use"

JANGAN langsung meminta konfirmasi.

Lakukan:

1. Identify process/container yang menggunakan port.
2. Determine apakah process tersebut bagian dari project.
3. Jika bukan bagian project, jangan mematikan process secara sembarangan.
4. Pilih host port alternatif yang tersedia.
5. Update configuration.
6. Restart/recreate container.
7. Validate connectivity.
8. Update documentation jika port berubah.

Jangan membunuh service existing hanya untuk membebaskan port kecuali memang
jelas bahwa service tersebut merupakan bagian dari project dan aman untuk
dihentikan.

---

## DOCKER STARTUP WORKFLOW

Gunakan workflow:

INSPECT PORTS
↓
IDENTIFY CONFLICTS
↓
SELECT AVAILABLE PORTS
↓
UPDATE CONFIGURATION
↓
BUILD DOCKER
↓
START CONTAINERS
↓
CHECK CONTAINER STATUS
↓
CHECK HEALTH
↓
TEST CONNECTIVITY
↓
FIX IF NEEDED
↓
DOCUMENT
↓
RECORD IN task_done.md

JANGAN:

BUILD
→ ERROR PORT
→ ASK USER

Jika masalah port dapat diselesaikan secara otomatis, selesaikan sendiri.

---

## PORT REGISTRY

Jika project memiliki banyak service, maintain daftar port yang digunakan
agar tidak terjadi collision.

Dokumentasikan pada:

`docs/deployment.md`

Contoh:

| Service    | Container Port | Host Port | Protocol |
| ---------- | -------------: | --------: | -------- |
| Backend    |           8000 |     18000 | TCP      |
| PostgreSQL |           5432 |     15432 | TCP      |
| Redis      |           6379 |     16379 | TCP      |
| Frontend   |           3000 |     13000 | TCP      |

Angka di atas hanya contoh.

Gunakan port aktual yang dipilih setelah melakukan availability check.

Jika terdapat service baru:

1. Check existing port registry.
2. Check host availability.
3. Select unused port.
4. Add it to the registry.
5. Update configuration.
6. Validate.

---

## RESUME / RECOVERY PORT CHECK

Saat melanjutkan project setelah:

- restart
- internet terputus
- session baru
- Docker restart
- computer restart

JANGAN mengasumsikan port sebelumnya masih tersedia.

Lakukan port check ulang sebelum menjalankan/recreate Docker.

Namun jangan mengganti port yang sudah digunakan project hanya karena ada
port lain yang tersedia.

PRIORITAS:

1. Existing project port configuration
2. Existing running container mapping
3. Existing documented port mapping
4. Host availability
5. Alternative port selection jika terjadi conflict

Tujuannya adalah menjaga port configuration tetap stabil antar-session,
tetapi tetap menghindari conflict.

---

## NO UNNECESSARY PORT CHANGES

Setelah port sudah dipilih dan project berjalan:

JANGAN mengganti port setiap kali agent dijalankan ulang.

Port hanya diganti jika:

- terjadi conflict
- configuration berubah
- architecture membutuhkan perubahan
- deployment environment membutuhkan perubahan

Dengan demikian frontend, backend, database, Docker, environment, dan
documentation tetap konsisten.
