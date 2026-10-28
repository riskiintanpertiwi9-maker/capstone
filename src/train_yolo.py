
"""
MoldGuard - Train YOLOv8 Model
Script untuk melatih model deteksi jamur menggunakan YOLOv8.
"""

import argparse
import os
from pathlib import Path

import yaml

# Root proyek: D:\capstone (dua level di atas file ini).
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache"
for _sub in ("ultralytics", "ultralytics/Ultralytics", "keras", "torch", "matplotlib"):
    (CACHE_DIR / _sub).mkdir(parents=True, exist_ok=True)

# Arahkan cache Ultralytics/Torch/Matplotlib ke drive D:.
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 for mold detection"
    )
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                        help="Pretrained model")
    parser.add_argument("--data", type=str,
                        default=str(BASE_DIR / "datasets" / "trained" / "data.yaml"),
                        help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=15,
                        help="Number of training epochs (default 15, hemat waktu CPU)")
    parser.add_argument("--imgsz", type=int, default=416,
                        help="Input image size")
    parser.add_argument("--batch", type=int, default=4,
                        help="Batch size")
    parser.add_argument("--device", type=str, default="",
                        help="Device: cuda or cpu; empty for automatic")
    parser.add_argument("--workers", type=int, default=2,
                        help="Number of dataloader workers")
    parser.add_argument("--project", type=str,
                        default=str(BASE_DIR / "results" / "yolo"),
                        help="Folder for training results")
    parser.add_argument("--name", type=str, default="train",
                        help="Experiment name")
    parser.add_argument("--patience", type=int, default=5,
                        help="Early stopping patience")
    parser.add_argument("--fraction", type=float, default=1.0,
                        help="Fraksi dataset yang dipakai (0-1), berguna untuk uji cepat")
    parser.add_argument("--cache", type=str, default="none",
                        choices=["none", "ram", "disk"],
                        help="Cache gambar agar epoch berikutnya lebih cepat")
    parser.add_argument("--lr0", type=float, default=None,
                        help="Learning rate awal (mis. 0.001 untuk fine-tuning)")
    return parser.parse_args()


def train(args):
    print("=" * 60)
    print("MoldGuard - YOLOv8 Training")
    print("=" * 60)

    data_path = Path(args.data)

    if not data_path.is_file():
        raise FileNotFoundError(
            f"File data.yaml tidak ditemukan: {data_path}"
        )

    with open(data_path, "r", encoding="utf-8") as f:
        data_cfg = yaml.safe_load(f)

    print(f"[INFO] Dataset   : {data_path}")
    print(f"[INFO] Classes   : {data_cfg['names']}")
    print(f"[INFO] Epochs    : {args.epochs}")
    print(f"[INFO] Image Size: {args.imgsz}")
    print(f"[INFO] Batch     : {args.batch}")
    print(f"[INFO] Device    : {args.device or 'automatic'}")

    model = YOLO(args.model)

    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device if args.device else None,
        workers=args.workers,
        project=args.project,
        name=args.name,
        patience=args.patience,
        exist_ok=True,
        fraction=args.fraction,
        cache=False if args.cache == "none" else args.cache,
        lr0=args.lr0 if args.lr0 else 0.01,
        save=True,
        plots=True,
        verbose=True,
        seed=42,
    )

    best_model = Path(args.project) / args.name / "weights" / "best.pt"

    print("\n[INFO] Training selesai!")
    print(f"[INFO] Model terbaik: {best_model}")
    print(f"[INFO] Model tersedia: {best_model.exists()}")

    return results


if __name__ == "__main__":
    args = parse_args()
    train(args)
