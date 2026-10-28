"""
MoldGuard — Flask Web Application
====================================
Website deteksi jamur dinding berbasis AI (YOLOv8 + MobileNetV2).

Endpoint:
  GET  /           → Beranda
  GET  /deteksi    → Halaman deteksi (upload/kamera)
  POST /predict    → Proses gambar dan jalankan model
  GET  /tentang    → Halaman tentang MoldGuard
  GET  /health     → Health check API
"""

import os
import uuid
import json
import base64
import logging
from pathlib import Path

import cv2
import numpy as np
from flask import (
    Flask, render_template, request,
    jsonify, redirect, url_for
)
from werkzeug.utils import secure_filename

# ── App Setup ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "web" / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

YOLO_MODEL_PATH   = BASE_DIR / "results" / "yolo" / "train" / "weights" / "best.pt"
MOBILE_MODEL_PATH = BASE_DIR / "models" / "mobilenet" / "best.pth"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

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
_device_str     = "cpu"

try:
    import torch
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _device_str = str(_device)
except ImportError:
    torch = None
    _device = None


def _yolo_available() -> bool:
    return YOLO_MODEL_PATH.exists()


def _mobile_available() -> bool:
    return MOBILE_MODEL_PATH.exists()


def _load_yolo():
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model
    from ultralytics import YOLO
    _yolo_model = YOLO(str(YOLO_MODEL_PATH))
    log.info("YOLOv8 model loaded.")
    return _yolo_model


def _load_mobile():
    global _mobile_model, _mobile_classes
    if _mobile_model is not None:
        return _mobile_model, _mobile_classes
    import torch
    import torch.nn as nn
    from torchvision import models as tv

    ckpt = torch.load(str(MOBILE_MODEL_PATH), map_location=_device)
    _mobile_classes = ckpt["classes"]
    num_cls = len(_mobile_classes)

    model = tv.mobilenet_v2(weights=None)
    in_f = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_f, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, num_cls),
    )
    model.load_state_dict(ckpt["state_dict"])
    model.to(_device).eval()
    _mobile_model = model
    log.info("MobileNetV2 model loaded. Classes: %s", _mobile_classes)
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
    model    = _load_yolo()
    results  = model.predict(img_bgr, conf=conf, verbose=False)
    annotated = results[0].plot()
    boxes     = results[0].boxes

    detections = []
    if boxes is not None:
        for box in boxes:
            detections.append({
                "class":      results[0].names[int(box.cls)],
                "confidence": round(float(box.conf), 4),
                "bbox":       [round(v, 1) for v in box.xyxy[0].tolist()],
            })
    return annotated, detections


def run_mobile_inference(img_bgr: np.ndarray):
    import torch
    from torchvision import transforms

    model, classes = _load_mobile()
    tf = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    rgb    = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    tensor = tf(rgb).unsqueeze(0).to(_device)
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0].cpu().numpy()
    return [{"class": c, "confidence": round(float(p), 4)} for c, p in zip(classes, probs)]


def determine_status(yolo_dets, mobile_results):
    """
    Tentukan status berdasarkan hasil model yang sesungguhnya.
    Returns: 'mold_detected' | 'no_mold' | 'uncertain'
    """
    has_mold_yolo = any(d["class"].lower() == "mold" for d in (yolo_dets or []))
    has_suspected  = any(d["class"].lower() == "suspected" for d in (yolo_dets or []))

    top_mobile = None
    if mobile_results:
        top_mobile = max(mobile_results, key=lambda x: x["confidence"])

    mobile_mold     = top_mobile and top_mobile["class"].lower() == "mold"     and top_mobile["confidence"] > 0.5
    mobile_clean    = top_mobile and top_mobile["class"].lower() == "clean"    and top_mobile["confidence"] > 0.5
    mobile_suspected = top_mobile and top_mobile["class"].lower() == "suspected" and top_mobile["confidence"] > 0.4

    if has_mold_yolo or mobile_mold:
        return "mold_detected"
    if has_suspected or mobile_suspected:
        return "uncertain"
    if mobile_clean and not has_mold_yolo and not has_suspected:
        return "no_mold"
    return "uncertain"


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def beranda():
    return render_template("beranda.html")


@app.route("/deteksi")
def deteksi():
    return render_template("deteksi.html")


@app.route("/tentang")
def tentang():
    return render_template("tentang.html")


@app.route("/hasil")
def hasil():
    """Halaman hasil statis (ditampilkan via JS setelah POST /predict berhasil)."""
    return render_template("hasil.html")


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

    conf = float(request.form.get("conf", 0.4))
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
        "status":          "uncertain",
        "original_image":  original_b64,
        "annotated_image": None,
        "yolo":            None,
        "mobilenet":       None,
        "yolo_available":  _yolo_available(),
        "mobile_available": _mobile_available(),
        "error_details":   [],
    }

    # ── YOLOv8 ──
    if _yolo_available():
        try:
            annotated, dets = run_yolo_inference(img_bgr, conf)
            resp["yolo"]            = dets
            resp["annotated_image"] = img_to_b64(annotated)
        except Exception as exc:
            log.exception("YOLO inference error")
            resp["error_details"].append(f"YOLO: {exc}")
    else:
        resp["error_details"].append("Model YOLOv8 belum tersedia. Latih model terlebih dahulu.")

    # ── MobileNetV2 ──
    if _mobile_available() and torch is not None:
        try:
            mobile_res     = run_mobile_inference(img_bgr)
            resp["mobilenet"] = mobile_res
            if resp["annotated_image"] is None:
                resp["annotated_image"] = original_b64
        except Exception as exc:
            log.exception("MobileNet inference error")
            resp["error_details"].append(f"MobileNetV2: {exc}")
    else:
        if torch is None:
            resp["error_details"].append("PyTorch tidak terinstal.")
        else:
            resp["error_details"].append("Model MobileNetV2 belum tersedia. Latih model terlebih dahulu.")

    # ── Tentukan status ──
    resp["status"] = determine_status(resp.get("yolo"), resp.get("mobilenet"))

    # Jika tidak ada model sama sekali → kembalikan status khusus
    if not _yolo_available() and not _mobile_available():
        resp["status"] = "model_unavailable"

    return jsonify(resp)


@app.route("/health")
def health():
    return jsonify({
        "status":           "ok",
        "device":           _device_str,
        "yolo_available":   _yolo_available(),
        "mobile_available": _mobile_available(),
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
    print(f"  YOLO tersedia : {_yolo_available()}")
    print(f"  MobileNet     : {_mobile_available()}")
    print("  URL           : http://127.0.0.1:5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=True)
