"""
MoldGuard - Evaluasi kandidat model YOLOv8 (train_v2).

Mengukur kualitas box pada split val/test, menguji false positive pada
dinding bersih (negative samples), dan menyimpan contoh visual prediksi.

Jalankan: python src/eval_yolo_v2.py
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache"
for _sub in ("ultralytics", "ultralytics/Ultralytics"):
    (CACHE_DIR / _sub).mkdir(parents=True, exist_ok=True)

os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

from ultralytics import YOLO

WEIGHTS = BASE_DIR / "results" / "yolo" / "train_v2" / "weights" / "best.pt"
DATA = BASE_DIR / "datasets" / "yolo" / "data.yaml"
OUT = BASE_DIR / "results" / "yolo" / "train_v2"
PREVIEW = OUT / "preview"


def eval_split(model, split):
    """Validasi pada satu split dataset."""
    print(f"\n=== Validasi split '{split}' ===")
    metrics = model.val(data=str(DATA), split=split, imgsz=416,
                        conf=0.5, iou=0.45, verbose=False, plots=False,
                        project=str(OUT), name=f"val_{split}")
    print(f"  precision : {metrics.box.mp:.4f}")
    print(f"  recall    : {metrics.box.mr:.4f}")
    print(f"  mAP50     : {metrics.box.map50:.4f}")
    print(f"  mAP50-95  : {metrics.box.map:.4f}")
    return metrics


def clean_wall_test(model, conf=0.5):
    """Hitung deteksi palsu pada gambar dinding tanpa jamur."""
    print("\n=== Uji false positive dinding bersih ===")
    candidates = []
    for base in (BASE_DIR / "datasets" / "trained" / "classifier",
                 BASE_DIR / "datasets" / "yolo" / "images" / "test"):
        if base.is_dir():
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                candidates.extend(p for p in base.rglob(ext)
                                  if "Normal Wall" in str(p) or "neg_" in p.name)
    candidates = sorted(set(candidates))
    if not candidates:
        print("  (tidak ada gambar negatif ditemukan)")
        return

    flagged = 0
    PREVIEW.mkdir(parents=True, exist_ok=True)
    for img in candidates:
        res = model.predict(str(img), conf=conf, iou=0.45, verbose=False)[0]
        n = 0 if res.boxes is None else len(res.boxes)
        if n:
            flagged += 1
            print(f"  FP  {img.name}: {n} box")
            res.save(filename=str(PREVIEW / f"fp_{img.stem}.jpg"))
    print(f"  Total gambar diuji : {len(candidates)}")
    print(f"  Gambar terdeteksi  : {flagged}")
    print(f"  Tingkat FP         : {flagged / len(candidates) * 100:.1f}%")


def visual_preview(model, limit=6):
    """Simpan contoh prediksi pada gambar val berjamur untuk cek ketatnya box."""
    print("\n=== Contoh prediksi (val) ===")
    img_dir = BASE_DIR / "datasets" / "yolo" / "images" / "val"
    imgs = [p for p in sorted(img_dir.glob("*")) if p.suffix.lower() in
            (".jpg", ".jpeg", ".png", ".webp") and not p.name.startswith("neg_")]
    PREVIEW.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(imgs[:limit]):
        res = model.predict(str(img), conf=0.5, iou=0.45, verbose=False)[0]
        n = 0 if res.boxes is None else len(res.boxes)
        res.save(filename=str(PREVIEW / f"val_{i}_{img.stem}.jpg"))
        print(f"  {img.name}: {n} box")


def main():
    if not WEIGHTS.is_file():
        raise SystemExit(f"Bobot tidak ditemukan: {WEIGHTS}")
    print(f"Model: {WEIGHTS}")
    model = YOLO(str(WEIGHTS))

    eval_split(model, "val")
    eval_split(model, "test")
    clean_wall_test(model, conf=0.5)
    visual_preview(model)

    print(f"\nPreview tersimpan di: {PREVIEW}")


if __name__ == "__main__":
    main()