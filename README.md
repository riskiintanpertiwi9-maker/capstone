# 🔬 MoldGuard — AI-Powered Mold Detection System

> Sistem deteksi dan klasifikasi jamur berbasis deep learning menggunakan **YOLOv8** (object detection) dan **MobileNetV2** (image classification).

---

## 📁 Struktur Proyek

```
D:\capstone\
│
├── datasets/
│   ├── yolo/                       # Deteksi: 1.785 train / 361 val / 376 test
│   │   ├── images/{train,val,test}/   # termasuk 40 negative dinding bersih
│   │   ├── labels/{train,val,test}/
│   │   └── data.yaml               # nc=1, names=['mold']
│   │
│   └── classification/             # Klasifikasi 5 kelas
│       ├── train/{aspfla,aspfum,clado,fussp,peni}/
│       ├── val/{aspfla,aspfum,clado,fussp,peni}/
│       └── test/{aspfla,aspfum,clado,fussp,peni}/
│
├── models/
│   ├── mobilenet/
│   │   ├── mobilenet_mold.h5            # Checkpoint Keras MobileNetV2 (5 kelas)
│   │   └── mobilenet_mold.labels.json   # Urutan nama kelas classifier
│   └── yolo/
│       └── yolov8n.pt                   # Bobot pretrained YOLOv8n
│
├── src/
│   ├── train_yolo.py            # Training YOLOv8
│   ├── train_mobilenet_keras.py # Training MobileNetV2 (Keras)
│   ├── promote_yolo.py          # Evaluasi + promosi checkpoint YOLO
│   └── predict.py               # Inference CLI (.h5 + YOLO)
│
├── results/
│   ├── yolo/train/weights/best.pt   # Model YOLO yang dipakai web
│   ├── yolo/train_*/                # Riwayat eksperimen training
│   └── mobilenet/train_*/           # Checkpoint + metrik training classifier
│
├── utils/
│   └── class_names.py           # Sidecar label kelas classifier
│
├── web/
│   ├── app.py                   # Flask web application
│   ├── templates/               # beranda, deteksi, hasil, tentang
│   └── static/
│       ├── css/style.css        # Tema hijau (moss green)
│       ├── js/script.js
│       └── uploads/             # Gambar yang diunggah
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Instalasi

### 1. Clone & masuk ke direktori

```bash
cd D:\capstone
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

Proyek ini hanya memakai dua dataset:

### 1. `datasets/yolo/` — deteksi area jamur

- 1 kelas: `mold`
- Train 1.785 gambar, val 361, test 376
- Train berisi **40 negative** (dinding bersih tanpa jamur) agar model tidak
  menandai dinding bersih sebagai jamur.

Format label YOLO (`class_id cx cy w h`, semua ternormalisasi 0–1):
```
0 0.512 0.483 0.234 0.312
```

### 2. `datasets/classification/` — klasifikasi spesies

- 5 kelas: `aspfla`, `aspfum`, `clado`, `fussp`, `peni`
- Train 2.976 gambar, val 630, test 678
- Tidak ada kelas `Normal Wall`; penentuan dinding bersih sepenuhnya
  mengandalkan YOLO.

---

## 🚀 Training

### YOLOv8

```bash
# Fine-tuning dari model yang sudah ada, dataset penuh + negative dinding bersih
python src/train_yolo.py --model results/yolo/train/weights/best.pt ^
  --data datasets/yolo/data.yaml ^
  --epochs 30 --imgsz 416 --batch 16 --patience 10 ^
  --fraction 1.0 --optimizer AdamW --lr0 0.0015 ^
  --cache ram --device cpu --name train_v5
```

Output tersimpan di `results/yolo/<name>/`. Evaluasi dan promosi ke model web:

```bash
python src/promote_yolo.py --candidate results/yolo/train_v5/weights/best.pt --conf 0.6
```

`promote_yolo.py` menguji val/test, menghitung false positive pada gambar
negative dinding bersih, membackup model lama ke `best_prev.pt`, lalu menyalin
kandidat ke `results/yolo/train/weights/best.pt`.

| Argumen      | Default                        | Keterangan                        |
|--------------|--------------------------------|-----------------------------------|
| `--model`    | `models/yolo/yolov8n.pt`       | Pretrained / checkpoint awal      |
| `--data`     | `datasets/yolo/data.yaml`      | Dataset YOLO (1 kelas `mold`)     |
| `--epochs`   | 15                             | Jumlah epoch                      |
| `--imgsz`    | 416                            | Ukuran input gambar               |
| `--batch`    | 4                              | Batch size                        |
| `--patience` | 5                              | Early stopping                    |
| `--fraction` | 1.0                            | Fraksi dataset (0-1)              |
| `--optimizer`| `auto`                         | `auto` mengabaikan `--lr0`        |
| `--lr0`      | -                              | Learning rate awal (fine-tuning)  |
| `--device`   | auto                           | `cuda` atau `cpu`                 |
| `--cache`    | `none`                         | `ram`/`disk` untuk mempercepat    |

### MobileNetV2 (Keras — model yang dipakai web)

```bash
python src/train_mobilenet_keras.py --data datasets/classification ^
  --reset-labels --epochs 25 --batch 16 --patience 8 --name train_5class
```

`--reset-labels` menimpa sidecar `mobilenet_mold.labels.json` agar cocok
dengan 5 folder kelas dataset.

| Argumen          | Default                                    | Keterangan                 |
|------------------|--------------------------------------------|----------------------------|
| `--epochs`       | 15                                         | Jumlah epoch               |
| `--batch`        | 8                                          | Batch size                 |
| `--lr`           | 1e-4                                       | Learning rate              |
| `--data`         | `datasets/classification`                  | Folder train/ val/ test/   |
| `--labels`       | `models/mobilenet/mobilenet_mold.labels.json` | Sidecar urutan kelas    |
| `--output`       | `models/mobilenet/mobilenet_mold.h5`       | Checkpoint hasil training  |
| `--reset-labels` | -                                          | Timpa sidecar label        |
| `--eval-only`    | -                                          | Evaluasi tanpa training    |

Metrik & plot tersimpan di `results/mobilenet/<name>/`.

---

## 🔍 Inference / Prediksi

```bash
# YOLO saja
python src/predict.py --source gambar.jpg --mode yolo

# MobileNet saja (klasifikasi seluruh gambar)
python src/predict.py --source gambar.jpg --mode mobilenet

# Keduanya
python src/predict.py --source gambar.jpg --mode both --save

# Seluruh folder
python src/predict.py --source datasets/yolo/images/test --mode both --save
```

---

## 📊 Evaluasi

Evaluasi YOLO + promosi model dilakukan oleh:

```bash
python src/promote_yolo.py --candidate results/yolo/train_v5/weights/best.pt --conf 0.6
```

Ringkasan metrik model deployed: `results/yolo/train/metrics_summary.json`.
Riwayat per-epoch: `results/yolo/<name>/results.csv`.
Evaluasi classifier: `results/mobilenet/<name>/metrics_val.json` dan
`metrics_test.json`.

---

## 🌐 Web Application

```bash
python web/app.py
```

Buka browser: **http://127.0.0.1:5000**

Backend memuat:
- `results/yolo/train/weights/best.pt` (YOLOv8, 1 kelas `mold`)
- `models/mobilenet/mobilenet_mold.h5` + sidecar label (Keras, 5 kelas)

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

### Klasifikasi (MobileNetV2) — 5 kelas
| Folder | Nama tampilan |
|--------|---------------|
| `aspfla` | Aspergillus flavus |
| `aspfum` | Aspergillus fumigatus |
| `clado`  | Cladosporium spp |
| `fussp`  | Fusarium spp |
| `peni`   | Penicillium spp |

> Status web hanya `mold_detected` atau `no_mold`:
> - `mold_detected` bila YOLO menemukan minimal satu box yang lolos filter.
> - `no_mold` bila tidak ada box.
>
> Dataset classifier tidak memiliki kelas dinding bersih, sehingga hasil
> MobileNet hanya dipakai untuk menamai spesies di dalam box YOLO. Dinding
> bersih tidak akan pernah dilaporkan berjamur karena YOLO tidak menghasilkan
> box pada gambar tersebut (dibantu 40 negative saat training).

---

## 🛠️ Tech Stack

- **YOLOv8** — Ultralytics (Object Detection)
- **MobileNetV2** — TensorFlow / Keras (Classification)
- **Flask** — Web backend
- **OpenCV** — Image processing
- **PyTorch** — Backend YOLO

---

## 📝 Lisensi

MIT License © 2024 MoldGuard