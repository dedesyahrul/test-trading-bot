# Frontend Runtime Error: `reportAllChanges`


Error berikut:

```text
Uncaught TypeError: Cannot read properties of undefined (reading 'startTime')
at et.reportAllChanges (<anonymous>)
```

berasal dari script yang di-inject browser atau extension. Indikatornya adalah stack frame `VM561` dan fungsi `reportAllChanges`; fungsi tersebut tidak terdapat di source atau bundle frontend MemeX.

Frontend MemeX berhasil dibuild tanpa error:

```powershell
npm run build
```

## Resolution

1. Buka DevTools dengan `Ctrl+Shift+P` lalu pilih `Disable JavaScript` untuk memastikan error bukan dari aplikasi.
2. Buka halaman menggunakan Incognito tanpa extension.
3. Jika error hilang, nonaktifkan extension yang memonitor performance, web vitals, accessibility, atau developer tools.
4. Hapus cache site dan lakukan hard reload dengan `Ctrl+Shift+R`.
5. Pastikan error tidak muncul dari tab extension melalui `chrome://extensions` atau `edge://extensions`.

## Verification

Tidak ada pemanggilan berikut pada source aplikasi MemeX:

- `reportAllChanges`
- `web-vitals`
- `PerformanceObserver` custom

Error tersebut tidak dapat diperbaiki dari komponen Vue karena terjadi di execution context terpisah milik browser/extension.
