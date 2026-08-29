# MemeX — Prediction Engine

> Dokumen ini menjelaskan rancangan Machine Learning Pipeline untuk memperkirakan probabilitas pergerakan harga jangka pendek.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Problem Formulation](#2-problem-formulation)
- [3. Target Variables](#3-target-variables)
- [4. ML Pipeline Architecture](#4-ml-pipeline-architecture)
- [5. Model Selection](#5-model-selection)
- [6. Evaluation Metrics](#6-evaluation-metrics)
- [7. Serving & Output](#7-serving--output)

---

## 1. Overview

Prediction Engine bertugas menerima *computed features* dari token yang lolos Risk Engine, kemudian menggunakan Machine Learning model untuk menghasilkan skor probabilitas pergerakan harga. 

**Prinsip Utama:** Model ML tidak mengambil keputusan trading, melainkan hanya mengeluarkan probabilitas statistik (misal: "Kemungkinan harga naik 10% dalam 15 menit adalah 65%").

---

## 2. Problem Formulation

Trading meme coin memiliki karakteristik *high noise* dan *extreme volatility*. Memprediksi harga eksak (Regression) hampir tidak mungkin dan sangat error-prone. Oleh karena itu, problem ini diformulasikan sebagai **Binary Classification**.

**Question:** *Diberikan kondisi pasar saat ini ($T_0$), apakah token akan mencapai target profit $X$% sebelum menyentuh stop loss $Y$% dalam jangka waktu maksimal $Z$ menit?*

---

## 3. Target Variables

Target prediksi (`y`) dibuat berdasarkan kondisi riil yang dapat dieksekusi oleh trading engine.

### Target 1: Momentum Scalp (5m - 15m)
- **Kondisi Positif (1):** High price menyentuh +15% dari entry price sebelum Low price menyentuh -10%, dalam kurun waktu 15 menit.
- **Kondisi Negatif (0):** Lainnya (terkena SL -10% lebih dulu, atau tidak mencapai target dalam waktu 15 menit).

### Target 2: Volume Breakout (1h)
- **Kondisi Positif (1):** High price menyentuh +30% dari entry price sebelum Low price menyentuh -15%, dalam kurun waktu 60 menit.
- **Kondisi Negatif (0):** Lainnya.

---

## 4. ML Pipeline Architecture

```mermaid
graph TD
    subgraph Offline [Offline Training]
        DB[(Historical Features & Prices)] -->|Extract| TS[Train/Test Split]
        TS -->|Time-series Split| Labeling[Target Generation]
        Labeling --> Training[Model Training]
        Training --> Eval[Evaluation]
        Eval -->|Save| Registry[Model Registry (Artifacts)]
    end

    subgraph Online [Online Inference]
        FW[Feature Worker] --> Inference[Inference Engine]
        Registry -->|Load Model| Inference
        Inference -->|Probability Score| SignalWorker[Signal Engine]
    end
```

---

## 5. Model Selection

Untuk fase awal, **Deep Learning TIDAK direkomendasikan** karena lambat dilatih, mudah overfitting pada data noisy, dan sulit diinterpretasi (blackbox).

**Rekomendasi Model:**
1. **LightGBM / XGBoost:** (Pilihan Utama)
   - Sangat cepat untuk training dan inference.
   - Handal menangani tabular data.
   - Menyediakan feature importance yang jelas.
2. **Logistic Regression:** (Sebagai Baseline)
   - Digunakan sebagai pembanding. Jika LightGBM tidak mengalahkan Logistic Regression secara signifikan, berarti signal di data masih terlalu lemah.

---

## 6. Evaluation Metrics

Evaluasi dalam trading ML berbeda dengan standar machine learning biasa. Akurasi global (Accuracy) bisa menyesatkan karena ketidakseimbangan kelas (class imbalance).

### Metrik Evaluasi Wajib:
1. **Precision (pada threshold tinggi):** Kita ingin meminimalkan False Positive (membeli token yang ujungnya turun). Precision di atas 60-70% pada top 10% highest confidence predictions adalah target utama.
2. **PR-AUC (Precision-Recall Area Under Curve):** Lebih relevan dibanding ROC-AUC untuk dataset imbalanced.
3. **Expected Value / Profitability Simulation:** Simulasi profit kotor dari sinyal True Positive dikurangi kerugian dari False Positive.

---

## 7. Serving & Output

Inference dilakukan secara real-time via ARQ worker.

**Contoh Output dari Prediction Engine:**

```json
{
  "pair_id": "uuid-here",
  "predicted_at": "2026-08-29T15:05:00Z",
  "model_version": "lightgbm-momentum-v1",
  "predictions": [
    {
      "target": "hit_15pct_before_minus_10pct_in_15m",
      "probability": 0.72
    },
    {
      "target": "hit_30pct_before_minus_15pct_in_60m",
      "probability": 0.45
    }
  ],
  "feature_snapshot_id": "uuid-feature-id"
}
```

Probabilitas ini kemudian diteruskan ke Strategy Engine untuk diambil keputusan `BUY`, `SELL`, atau `SKIP`.
