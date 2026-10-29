"""
MoldGuard — Flask Web Application
====================================
Website deteksi jamur dinding berbasis AI (YOLOv8 + MobileNetV2).

Endpoint:
  GET  /                 → Beranda / dashboard
  GET  /deteksi          → Halaman deteksi (kamera/galeri)
  GET  /hasil            → Hasil deteksi (data dari browser)
  GET  /riwayat          → Riwayat pemeriksaan
  GET  /laporan          → Ringkasan & laporan
  GET  /edukasi          → Tips & edukasi
  GET  /edukasi/<slug>   → Detail artikel
  GET  /pengingat        → Pengingat perawatan
  GET  /profil           → Profil perangkat
  GET  /pengaturan       → Preferensi aplikasi
  GET  /tentang          → Tentang MoldGuard
  POST /predict          → Proses gambar dan jalankan model
  GET  /health           → Health check API
"""

import os
import uuid
import json
import base64
import logging
from pathlib import Path

# Arahkan cache YOLO/TensorFlow/Keras ke drive D: agar tidak menulis ke C:.
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache"
for _sub in ("ultralytics", "ultralytics/Ultralytics", "keras", "torch", "matplotlib"):
    (CACHE_DIR / _sub).mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))
os.environ.setdefault("KERAS_HOME", str(CACHE_DIR / "keras"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

import cv2
import numpy as np
from flask import (
    Flask, render_template, request,
    jsonify, redirect, url_for, abort
)
from werkzeug.utils import secure_filename

try:  # dijalankan sebagai paket (python -m web.app)
    from .articles import ARTICLES, ARTICLES_BY_SLUG, CATEGORIES
except ImportError:  # dijalankan langsung (python web/app.py)
    from articles import ARTICLES, ARTICLES_BY_SLUG, CATEGORIES

# ── App Setup ──────────────────────────────────────────────────────────────────
UPLOAD_DIR = BASE_DIR / "web" / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

YOLO_MODEL_PATH    = BASE_DIR / "results" / "yolo" / "train" / "weights" / "best.pt"
MOBILE_MODEL_PATH  = BASE_DIR / "models" / "mobilenet" / "mobilenet_mold.h5"
MOBILE_LABELS_PATH = BASE_DIR / "models" / "mobilenet" / "mobilenet_mold.labels.json"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB

# Preprocessing classifier: resize 224 → Gaussian blur → /255 (sama seperti training).
MOBILE_IMGSZ        = 224
MOBILE_BLUR_KERNEL  = 5
MAX_BOX_AREA        = 0.92   # box nyaris menutupi seluruh foto dianggap bukan jamur spesifik
YOLO_IMGSZ          = 416    # samakan dengan ukuran training

# Dataset classifier hanya berisi 5 jenis jamur (tanpa kelas dinding bersih).
# Kode folder dataset dipetakan ke nama yang ditampilkan di UI.
SPECIES_DISPLAY = {
    "aspfla": "Aspergillus flavus",
    "aspfum": "Aspergillus fumigatus",
    "clado":  "Cladosporium spp",
    "fussp":  "Fusarium spp",
    "peni":   "Penicillium spp",
}


def display_name(name: str) -> str:
    return SPECIES_DISPLAY.get(str(name).strip().lower(), str(name))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"]      = str(UPLOAD_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "moldguard-capstone-2024")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("moldguard")


# ── Model state ────────────────────────────────────────────────────────────────
_yolo_model     = None
_mobile_model   = None
_mobile_classes = None
_mobile_imgsz   = MOBILE_IMGSZ
_device_str     = "cpu"

try:
    import tensorflow as tf
    _tf_available = True
except Exception:  # noqa: BLE001 - TensorFlow opsional saat start
    tf = None
    _tf_available = False


def _yolo_available() -> bool:
    return YOLO_MODEL_PATH.exists()


def _mobile_available() -> bool:
    return MOBILE_MODEL_PATH.exists() and MOBILE_LABELS_PATH.exists()


def _load_yolo():
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model
    from ultralytics import YOLO
    _yolo_model = YOLO(str(YOLO_MODEL_PATH))
    log.info("YOLOv8 model loaded: %s", YOLO_MODEL_PATH)
    return _yolo_model


def _read_mobile_labels():
    payload = json.loads(MOBILE_LABELS_PATH.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("class_names")
    if not isinstance(payload, list) or not payload:
        raise ValueError("Sidecar label kelas tidak valid.")
    return [str(name).strip() for name in payload]


def _load_mobile():
    """Muat checkpoint Keras MobileNetV2 (.h5) dari hasil training."""
    global _mobile_model, _mobile_classes, _mobile_imgsz
    if _mobile_model is not None:
        return _mobile_model, _mobile_classes
    if not _tf_available:
        raise RuntimeError("TensorFlow tidak terinstal.")

    model   = tf.keras.models.load_model(str(MOBILE_MODEL_PATH), compile=False)
    classes = _read_mobile_labels()

    output_shape = model.output_shape
    if isinstance(output_shape, list):
        output_shape = output_shape[0]
    num_cls = int(output_shape[-1])
    if len(classes) != num_cls:
        raise ValueError(
            f"Jumlah label ({len(classes)}) tidak cocok dengan output model ({num_cls})."
        )

    input_shape = model.input_shape
    if isinstance(input_shape, list):
        input_shape = input_shape[0]
    if input_shape and input_shape[1]:
        _mobile_imgsz = int(input_shape[1])

    _mobile_model = model
    _mobile_classes = classes
    log.info("MobileNetV2 (.h5) loaded. imgsz=%d, classes=%s", _mobile_imgsz, classes)
    return _mobile_model, _mobile_classes


# ── Helpers ────────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def img_to_b64(img_bgr: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return base64.b64encode(buf).decode("utf-8")


def read_image_from_request(file_storage) -> np.ndarray:
    data = np.frombuffer(file_storage.read(), np.uint8)
    img  = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return img


def run_yolo_inference(img_bgr: np.ndarray, conf: float):
    """Jalankan YOLO; kembalikan deteksi + crop area untuk verifikasi classifier."""
    model   = _load_yolo()
    result  = model.predict(img_bgr, conf=conf, iou=0.30, imgsz=YOLO_IMGSZ,
                            max_det=30, verbose=False)[0]
    boxes   = result.boxes
    h, w    = img_bgr.shape[:2]
    img_area = float(h * w)

    detections, crops = [], []
    if boxes is not None:
        for box in boxes:
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if (x2 - x1) < 5 or (y2 - y1) < 5:
                continue
            # Box raksasa (nyaris seluruh foto) bukan deteksi jamur yang presisi.
            if ((x2 - x1) * (y2 - y1)) / img_area > MAX_BOX_AREA:
                continue
            # Bintik terlalu kecil (<0.06% gambar) biasanya noise tekstur.
            if ((x2 - x1) * (y2 - y1)) / img_area < 0.0006:
                continue
            detections.append({
                "class":      result.names[int(box.cls)],
                "confidence": round(float(box.conf), 4),
                "bbox":       [float(x1), float(y1), float(x2), float(y2)],
            })
            crops.append(img_bgr[y1:y2, x1:x2])
    return detections, crops


def draw_detections(img_bgr: np.ndarray, detections):
    """Gambar bounding box yang benar-benar lolos verifikasi."""
    out = img_bgr.copy()
    for det in detections:
        x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
        color = (80, 125, 60)  # BGR hijau moss
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f'{det["class"]} {det["confidence"] * 100:.0f}%'
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(out, (x1, max(0, y1 - th - 10)), (x1 + tw + 10, y1), color, -1)
        cv2.putText(out, label, (x1 + 5, max(12, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def _preprocess_crop(crop_bgr: np.ndarray) -> np.ndarray:
    """Samakan preprocessing dengan training: resize 224, blur, /255."""
    resized = cv2.resize(crop_bgr, (_mobile_imgsz, _mobile_imgsz),
                         interpolation=cv2.INTER_AREA)
    if MOBILE_BLUR_KERNEL > 1:
        resized = cv2.GaussianBlur(resized, (MOBILE_BLUR_KERNEL, MOBILE_BLUR_KERNEL), 0)
    return resized.astype(np.float32) / 255.0


def classify_crops(crops):
    """Klasifikasi tiap crop YOLO (menentukan spesies jamur pada box)."""
    if not crops:
        return []
    model, classes = _load_mobile()
    batch = np.stack([_preprocess_crop(c) for c in crops], axis=0)
    probs = model.predict(batch, verbose=0)
    return [
        {
            "class":      classes[int(np.argmax(p))],
            "confidence": float(np.max(p)),
            "probs":      p,
        }
        for p in probs
    ]


def run_mobile_inference(crop_probs):
    """Rata-rata probabilitas crop di dalam box (spesies jamur)."""
    model, classes = _load_mobile()
    probs = np.mean([p["probs"] for p in crop_probs], axis=0)
    return [{"class": display_name(c), "confidence": round(float(p), 4)}
            for c, p in zip(classes, probs)]


def determine_status(yolo_dets):
    """
    Tentukan status hanya dari deteksi YOLO.

    Dataset classifier hanya berisi 5 jenis jamur (tanpa kelas dinding bersih),
    sehingga klasifikasi global tidak boleh dipakai untuk menyatakan jamur.
    Dinding bersih aman karena YOLO tidak menghasilkan box di sana.

    Returns: 'mold_detected' | 'no_mold'
    """
    has_mold_yolo = any(
        str(d.get("class", "")).strip().lower() == "mold" for d in (yolo_dets or [])
    )
    return "mold_detected" if has_mold_yolo else "no_mold"


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
@app.route("/dashboard")
def beranda():
    return render_template("dashboard.html", page="dashboard", featured_article=ARTICLES[0])


@app.route("/deteksi")
def deteksi():
    return render_template("deteksi.html", page="deteksi")


@app.route("/hasil")
def hasil():
    """Halaman hasil. Data hasil dibaca dari browser (session/local storage)."""
    return render_template("hasil.html", page="hasil")


@app.route("/riwayat")
def riwayat():
    return render_template("riwayat.html", page="riwayat")


@app.route("/laporan")
def laporan():
    return render_template("laporan.html", page="laporan")


@app.route("/edukasi")
def edukasi():
    featured = next((a for a in ARTICLES if a.get("featured")), ARTICLES[0])
    return render_template(
        "edukasi.html", page="edukasi",
        articles=ARTICLES, categories=CATEGORIES, featured=featured,
    )


@app.route("/edukasi/<slug>")
def edukasi_detail(slug):
    article = ARTICLES_BY_SLUG.get(slug)
    if article is None:
        return redirect(url_for("edukasi"))
    related = [a for a in ARTICLES if a["slug"] != slug][:3]
    return render_template(
        "edukasi_detail.html", page="edukasi",
        article=article, related=related,
    )


@app.route("/pengingat")
def pengingat():
    return render_template("pengingat.html", page="pengingat")


@app.route("/profil")
def profil():
    return render_template("profil.html", page="profil")


@app.route("/pengaturan")
def pengaturan():
    return render_template("pengaturan.html", page="pengaturan")


@app.route("/tentang")
def tentang():
    return render_template("tentang.html", page="tentang")


@app.route("/predict", methods=["POST"])
def predict():
    # ── Validasi file ──
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file gambar yang dikirimkan."}), 400

    f = request.files["file"]
    if not f or f.filename == "":
        return jsonify({"error": "File kosong atau tidak ada nama file."}), 400

    if not allowed_file(f.filename):
        return jsonify({"error": "Format file tidak didukung. Gunakan PNG, JPG, JPEG, BMP, atau WEBP."}), 400

    conf = float(request.form.get("conf", 0.35))
    conf = max(0.1, min(0.9, conf))

    # ── Baca gambar ──
    try:
        img_bgr = read_image_from_request(f)
    except Exception as exc:
        return jsonify({"error": f"Gagal membaca gambar: {exc}"}), 400

    if img_bgr is None:
        return jsonify({"error": "Gambar tidak dapat dibaca. Pastikan file tidak rusak."}), 400

    # ── Encode gambar asli ──
    original_b64 = img_to_b64(img_bgr)

    resp = {
        "status":          "no_mold",
        "original_image":  original_b64,
        "annotated_image": None,
        "yolo":            None,
        "mobilenet":       None,
        "yolo_available":  _yolo_available(),
        "mobile_available": _mobile_available(),
        "error_details":   [],
    }

    # ── YOLOv8 + klasifikasi crop ──
    yolo_crops, crop_probs = [], []
    if _yolo_available():
        try:
            dets, yolo_crops = run_yolo_inference(img_bgr, conf)

            # Setiap box yang lolos filter YOLO adalah kandidat jamur.
            # Classifier hanya menentukan spesiesnya, tidak membuang box,
            # karena dataset classifier tidak punya kelas dinding bersih.
            if yolo_crops and _mobile_available() and _tf_available:
                per_crop = classify_crops(yolo_crops)
                for det, prob in zip(dets, per_crop):
                    det["species"] = display_name(prob["class"])
                    det["species_confidence"] = round(prob["confidence"], 4)
                crop_probs = per_crop

            resp["yolo"] = dets
            resp["annotated_image"] = img_to_b64(draw_detections(img_bgr, dets))
        except Exception as exc:
            log.exception("YOLO inference error")
            resp["error_details"].append(f"YOLO: {exc}")
    else:
        resp["error_details"].append("Model YOLOv8 belum tersedia. Latih model terlebih dahulu.")

    # ── MobileNetV2 (Keras .h5) — hanya spesies pada area yang terdeteksi ──
    if crop_probs and _mobile_available() and _tf_available:
        try:
            resp["mobilenet"] = run_mobile_inference(crop_probs)
        except Exception as exc:
            log.exception("MobileNet inference error")
            resp["error_details"].append(f"MobileNetV2: {exc}")
    elif not _tf_available:
        resp["error_details"].append("TensorFlow tidak terinstal.")
    elif not _mobile_available():
        resp["error_details"].append("Model MobileNetV2 belum tersedia. Latih model terlebih dahulu.")

    # Gambar asli tetap ditampilkan walau tanpa anotasi.
    if resp["annotated_image"] is None:
        resp["annotated_image"] = original_b64

    # ── Tentukan status ──
    resp["status"] = determine_status(resp.get("yolo"))

    # Jika tidak ada model sama sekali → kembalikan status khusus
    if not _yolo_available() and not _mobile_available():
        resp["status"] = "model_unavailable"

    return jsonify(resp)


@app.route("/health")
def health():
    classes = _mobile_classes
    if not classes and MOBILE_LABELS_PATH.exists():
        try:
            classes = _read_mobile_labels()
        except Exception:  # noqa: BLE001 - health check tidak boleh gagal
            classes = []
    return jsonify({
        "status":           "ok",
        "device":           _device_str,
        "yolo_available":   _yolo_available(),
        "mobile_available": _mobile_available(),
        "mobile_backend":   "keras-tensorflow",
        "mobile_classes":   classes or [],
        "yolo_model":       str(YOLO_MODEL_PATH),
        "mobile_model":     str(MOBILE_MODEL_PATH),
    })


# ── Error handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Ukuran file melebihi batas 16MB."}), 413


@app.errorhandler(404)
def not_found(_):
    return redirect(url_for("beranda"))


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  MoldGuard — Deteksi Jamur Dinding")
    print(f"  Device        : {_device_str}")
    print(f"  YOLO tersedia : {_yolo_available()}  ({YOLO_MODEL_PATH})")
    print(f"  MobileNet     : {_mobile_available()}  ({MOBILE_MODEL_PATH})")
    print("  URL           : http://127.0.0.1:5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=False, use_reloader=False)
