"""
MoldGuard - Promosikan checkpoint YOLO terbaik ke model deployed.

Langkah:
1. Validasi kandidat pada split val & test (mAP, precision, recall).
2. Uji false positive pada gambar dinding bersih.
3. Backup model lama lalu salin kandidat ke results/yolo/train/weights/best.pt.
4. Simpan ringkasan metrik ke results/yolo/train/metrics_summary.json.

Contoh:
    python src/promote_yolo.py --candidate results/yolo/train_v5/weights/best.pt
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache"
for _sub in ("ultralytics", "ultralytics/Ultralytics", "matplotlib"):
    (CACHE_DIR / _sub).mkdir(parents=True, exist_ok=True)

os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

from ultralytics import YOLO

DATA = BASE_DIR / "datasets" / "yolo" / "data.yaml"
DEPLOY = BASE_DIR / "results" / "yolo" / "train" / "weights" / "best.pt"
SUMMARY = BASE_DIR / "results" / "yolo" / "train" / "metrics_summary.json"
NEG_ROOTS = [
    BASE_DIR / "datasets" / "yolo" / "images" / split for split in ("val", "test", "train")
]


def clean_wall_images():
    """Gambar dinding bersih = negative `neg_*` pada dataset YOLO."""
    imgs = []
    for root in NEG_ROOTS:
        if root.is_dir():
            imgs.extend(p for p in root.glob("neg_*") if p.is_file())
    return sorted(set(imgs))


def evaluate(model, conf):
    out = {}
    for split in ("val", "test"):
        m = model.val(data=str(DATA), split=split, imgsz=416,
                      verbose=False, plots=False,
                      project=str(BASE_DIR / "results" / "yolo" / "promote"),
                      name=f"val_{split}")
        out[split] = {
            "precision": round(float(m.box.mp), 4),
            "recall": round(float(m.box.mr), 4),
            "mAP50": round(float(m.box.map50), 4),
            "mAP50_95": round(float(m.box.map), 4),
        }

    imgs = clean_wall_images()
    flagged = 0
    detections = 0
    for img in imgs:
        res = model.predict(str(img), conf=conf, iou=0.30, imgsz=416, verbose=False)[0]
        n = 0 if res.boxes is None else len(res.boxes)
        if n:
            flagged += 1
            detections += n
    out["clean_wall"] = {
        "images": len(imgs),
        "flagged_images": flagged,
        "total_boxes": detections,
        "conf_threshold": conf,
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--conf", type=float, default=0.6)
    ap.add_argument("--skip-copy", action="store_true")
    args = ap.parse_args()

    candidate = Path(args.candidate)
    if not candidate.is_file():
        raise SystemExit(f"Kandidat tidak ditemukan: {candidate}")

    print(f"Evaluasi kandidat: {candidate}")
    model = YOLO(str(candidate))
    metrics = evaluate(model, args.conf)

    print(json.dumps(metrics, indent=2))

    print("\nUji dinding bersih:")
    cw = metrics["clean_wall"]
    print(f"  {cw['flagged_images']}/{cw['images']} gambar terdeteksi "
          f"({cw['total_boxes']} box) pada conf {cw['conf_threshold']}")

    if args.skip_copy:
        print("\n--skip-copy aktif: bobot tidak dipromosikan.")
        return

    if DEPLOY.is_file():
        backup = DEPLOY.with_name("best_prev.pt")
        shutil.copy2(DEPLOY, backup)
        print(f"Backup model lama -> {backup}")

    DEPLOY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate, DEPLOY)
    print(f"Model baru dipromosikan -> {DEPLOY}")

    metrics["promoted_at"] = datetime.now().isoformat(timespec="seconds")
    metrics["candidate"] = str(candidate)
    SUMMARY.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Ringkasan metrik -> {SUMMARY}")


if __name__ == "__main__":
    main()