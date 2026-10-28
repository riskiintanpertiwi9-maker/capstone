# 🔬 MoldGuard — AI-Powered Mold Detection System

> Sistem deteksi dan klasifikasi jamur berbasis deep learning menggunakan **YOLOv8** (object detection) dan **MobileNetV2** (image classification).

---

## 📁 Struktur Proyek

```
D:\capstone\
│
├── datasets/
│   ├── trained/                # Dataset yang benar-benar dipakai model deployed
│   │   ├── yolo/               # 72 train / 18 val + label YOLO
│   │   │   ├── images/{train,val}/
│   │   │   └── labels/{train,val}/
│   │   ├── classifier/         # 9 kelas, 72 train / 18 val
│   │   │   ├── train/<kelas>/
│   │   │   └── val/<kelas>/
│   │   └── data.yaml           # Konfigurasi dataset YOLO
│   │
│   ├── yolo/                   # Dataset besar (perlu `git lfs pull`)
│   └── classification/         # Dataset besar 5 kelas (perlu `git lfs pull`)
│
├── models/
│   └── mobilenet/
│       ├── mobilenet_mold.h5            # Checkpoint Keras MobileNetV2
│       └── mobilenet_mold.labels.json   # Urutan 9 nama kelas
│
├── src/
│   ├── train_yolo.py           # Training YOLOv8
│   ├── train_mobilenet_keras.py# Training MobileNetV2 (Keras, sesuai model deployed)
│   ├── train_mobilenet.py      # Alternatif training MobileNetV2 (PyTorch)
│   ├── predict.py              # Inference / prediksi (.h5 & .pth)
│   └── evaluate.py             # Evaluasi model (.h5 & .pth)
│
├── results/
│   ├── yolo/train/             # weights/best.pt + metrik & plot training
│   └── mobilenet/train/        # best.keras + metrik & plot training
│
├── utils/
│   └── class_names.py          # Sidecar label kelas classifier
│
├── web/
│   ├── app.py                  # Flask web application
│   ├── templates/              # beranda, deteksi, hasil, tentang
│   └── static/
│       ├── css/style.css       # Tema hijau (moss green)
│       ├── js/script.js
│       └── uploads/            # Gambar yang diunggah
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Instalasi

### 1. Clone & masuk ke direktori

```bash
cd MoldGuard
```

### 2. Buat virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🗂️ Dataset

Model yang dideploy dilatih dengan dataset di `datasets/trained/`:

```
datasets/trained/
├── yolo/                       # 72 gambar train / 18 val
│   ├── images/{train,val}/
│   └── labels/{train,val}/
├── classifier/                 # 9 kelas, 72 train / 18 val
│   ├── train/<kelas>/
│   └── val/<kelas>/
└── data.yaml                   # nc=1, names=['mold']
```

Format label YOLO (`class_id cx cy w h`, semua ternormalisasi 0–1):
```
0 0.512 0.483 0.234 0.312
```

`datasets/yolo/` dan `datasets/classification/` adalah dataset besar (5 kelas)
yang filenya disimpan via Git LFS. Jalankan `git lfs pull` bila ingin memakainya.

---

## 🚀 Training

### YOLOv8

```bash
python src/train_yolo.py --epochs 15 --imgsz 416 --batch 8
```

Default diarahkan ke `datasets/trained/data.yaml` dan output `results/yolo/train/`.

| Argumen   | Default                        | Keterangan              |
|-----------|--------------------------------|-------------------------|
| `--model` | `yolov8n.pt`                   | Pretrained backbone     |
| `--epochs`| 15                             | Jumlah epoch (hemat CPU)|
| `--imgsz` | 416                            | Ukuran input gambar     |
| `--batch` | 8                              | Batch size              |
| `--device`| auto                           | `cuda` atau `cpu`       |
| `--cache` | `none`                         | `ram`/`disk` untuk cepat|

### MobileNetV2 (Keras — model yang dipakai web)

```bash
python src/train_mobilenet_keras.py --epochs 15 --batch 8
```

| Argumen      | Default                                    | Keterangan              |
|--------------|--------------------------------------------|-------------------------|
| `--epochs`   | 15                                         | Jumlah epoch            |
| `--batch`    | 8                                          | Batch size              |
| `--lr`       | 1e-4                                       | Learning rate           |
| `--data`     | `datasets/trained/classifier`              | Folder train/ val/      |
| `--labels`   | `models/mobilenet/mobilenet_mold.labels.json` | Sidecar urutan kelas |
| `--output`   | `models/mobilenet/mobilenet_mold.h5`       | Checkpoint hasil training|
| `--eval-only`| -                                          | Evaluasi tanpa training |

Metrik & plot tersimpan di `results/mobilenet/train_run/`.

---

## 🔍 Inference / Prediksi

```bash
# YOLO saja
python src/predict.py --source gambar.jpg --mode yolo

# MobileNet saja
python src/predict.py --source gambar.jpg --mode mobilenet

# Keduanya
python src/predict.py --source gambar.jpg --mode both --save

# Seluruh folder
python src/predict.py --source datasets/trained/yolo/images/val --mode both --save
```

---

## 📊 Evaluasi

```bash
# Evaluasi YOLO
python src/evaluate.py --mode yolo

# Evaluasi MobileNet
python src/evaluate.py --mode mobilenet

# Keduanya
python src/evaluate.py --mode both
```

Hasil evaluasi disimpan di `results/yolo/` dan `results/mobilenet/`.

---

## 🌐 Web Application

```bash
python web/app.py
```

Buka browser: **http://127.0.0.1:5000**

Backend memuat:
- `results/yolo/train/weights/best.pt` (YOLOv8, 1 kelas `mold`)
- `models/mobilenet/mobilenet_mold.h5` + sidecar label (Keras, 9 kelas)

Fitur:
- 📁 Drag & drop upload gambar
- 🎯 Deteksi area jamur dengan YOLO
- 🧪 Klasifikasi spesies dari crop area jamur dengan MobileNetV2
- 📊 Visualisasi bounding box + probabilitas tiap kelas

---

## 📈 Kelas Dataset

### Deteksi (YOLOv8) — 1 kelas
| ID | Nama | Deskripsi |
|----|------|-----------|
| 0  | `mold` | Area jamur pada dinding |

### Klasifikasi (MobileNetV2) — 9 kelas
| ID | Nama |
|----|------|
| 0  | `Alternaria spp` |
| 1  | `Aspergillus` |
| 2  | `Chaetomium globosum` |
| 3  | `Cladosporium spp` |
| 4  | `Normal Wall` |
| 5  | `Penicillium chrysogenum` |
| 6  | `Stachybotrys chartarum` |
| 7  | `Trichoderma spp` |
| 8  | `Wallemia spp` |

> Status web (`mold_detected` / `no_mold` / `uncertain`) ditentukan dari
> deteksi YOLO dan prediksi MobileNet. `Normal Wall` dengan confidence > 0.5
> dianggap bersih; kelas jamur lain dengan confidence > 0.5 dianggap jamur.

### Hasil training (model deployed)

**YOLOv8** — `results/yolo/train/metrics_summary.json`
- mAP@0.5: **0.995**

**MobileNetV2** — `results/mobilenet/train/metrics_val.json`
- Validation accuracy: **0.8333** (18 gambar val)

---

## 🛠️ Tech Stack

- **YOLOv8** — Ultralytics (Object Detection)
- **MobileNetV2** — TensorFlow / Keras (Classification)
- **Flask** — Web backend
- **OpenCV** — Image processing
- **scikit-learn** — Metrics & evaluation
- **PyTorch** — Alternatif training classifier

---

## 📝 Lisensi

MIT License © 2024 MoldGuard
