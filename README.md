# 🔬 MoldGuard — AI-Powered Mold Detection System

> Sistem deteksi dan klasifikasi jamur berbasis deep learning menggunakan **YOLOv8** (object detection) dan **MobileNetV2** (image classification).

---

## 📁 Struktur Proyek

```
MoldGuard/
│
├── .venv/                      # Virtual environment Python
│
├── datasets/
│   ├── yolo/                   # Dataset untuk YOLOv8
│   │   ├── images/{train,val,test}/
│   │   ├── labels/{train,val,test}/
│   │   └── data.yaml           # Konfigurasi dataset YOLO
│   │
│   └── classification/         # Dataset untuk MobileNetV2
│       ├── train/
│       ├── val/
│       └── test/
│
├── models/
│   ├── yolo/                   # Model YOLO tersimpan
│   └── mobilenet/              # best.pth tersimpan
│
├── src/
│   ├── train_yolo.py           # Training YOLOv8
│   ├── train_mobilenet.py      # Training MobileNetV2
│   ├── predict.py              # Inference / prediksi
│   └── evaluate.py             # Evaluasi model
│
├── results/
│   ├── yolo/                   # Hasil training & evaluasi YOLO
│   └── mobilenet/              # Hasil training & evaluasi MobileNet
│
├── web/
│   ├── app.py                  # Flask web application
│   ├── templates/index.html    # Halaman utama
│   └── static/
│       ├── css/style.css
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

## 🗂️ Persiapan Dataset

### Dataset YOLO (Object Detection)

Letakkan gambar dan label di:
```
datasets/yolo/images/train/   ← gambar training
datasets/yolo/images/val/     ← gambar validasi
datasets/yolo/images/test/    ← gambar testing
datasets/yolo/labels/train/   ← label .txt (format YOLO)
datasets/yolo/labels/val/
datasets/yolo/labels/test/
```

Format label YOLO (`class_id cx cy w h`, semua ternormalisasi 0–1):
```
0 0.512 0.483 0.234 0.312
```

Edit `datasets/yolo/data.yaml` jika ingin menambah/mengubah kelas.

### Dataset Klasifikasi (MobileNetV2)

Struktur folder `ImageFolder` PyTorch:
```
datasets/classification/
├── train/
│   ├── clean/
│   ├── mold/
│   └── suspected/
├── val/
│   └── ...
└── test/
    └── ...
```

---

## 🚀 Training

### YOLOv8

```bash
python src/train_yolo.py \
  --model yolov8n.pt \
  --epochs 100 \
  --imgsz 640 \
  --batch 16
```

| Argumen   | Default                     | Keterangan              |
|-----------|-----------------------------|-------------------------|
| `--model` | `yolov8n.pt`                | Pretrained backbone      |
| `--epochs`| 100                         | Jumlah epoch            |
| `--imgsz` | 640                         | Ukuran input gambar     |
| `--batch` | 16                          | Batch size              |
| `--device`| auto                        | `cuda` atau `cpu`       |

### MobileNetV2

```bash
python src/train_mobilenet.py \
  --epochs 30 \
  --batch 32 \
  --lr 1e-3
```

| Argumen      | Default                        | Keterangan              |
|--------------|--------------------------------|-------------------------|
| `--epochs`   | 30                             | Jumlah epoch            |
| `--batch`    | 32                             | Batch size              |
| `--lr`       | 1e-3                           | Learning rate           |
| `--freeze`   | False                          | Freeze backbone layers  |
| `--model_out`| `models/mobilenet/best.pth`    | Path simpan model       |

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
python src/predict.py --source datasets/yolo/images/test --mode both --save
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
cd web
python app.py
```

Buka browser: **http://127.0.0.1:5000**

Fitur:
- 📁 Drag & drop upload gambar
- 🎯 Pilih mode: YOLO / MobileNet / Keduanya
- 🎚️ Atur confidence threshold
- 📊 Visualisasi hasil deteksi real-time

---

## 📈 Kelas Default

| ID | Nama       | Deskripsi                |
|----|------------|--------------------------|
| 0  | `mold`     | Terdeteksi ada jamur     |
| 1  | `clean`    | Bersih / bebas jamur     |
| 2  | `suspected`| Dicurigai ada jamur      |

---

## 🛠️ Tech Stack

- **YOLOv8** — Ultralytics (Object Detection)
- **MobileNetV2** — PyTorch + TorchVision (Classification)
- **Flask** — Web backend
- **OpenCV** — Image processing
- **scikit-learn** — Metrics & evaluation

---

## 📝 Lisensi

MIT License © 2024 MoldGuard
