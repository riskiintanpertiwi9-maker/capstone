
"""
MoldGuard - Train YOLOv8 Model
Script untuk melatih model deteksi jamur menggunakan YOLOv8.
"""

import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 for mold detection"
    )
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                        help="Pretrained model")
    parser.add_argument("--data", type=str,
                        default=r"D:\MoldGuard\datasets\yolo\data.yaml",
                        help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=25,
                        help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=512,
                        help="Input image size")
    parser.add_argument("--batch", type=int, default=4,
                        help="Batch size")
    parser.add_argument("--device", type=str, default="",
                        help="Device: cuda or cpu; empty for automatic")
    parser.add_argument("--workers", type=int, default=2,
                        help="Number of dataloader workers")
    parser.add_argument("--project", type=str,
                        default=r"D:\MoldGuard\runs\detect",
                        help="Folder for training results")
    parser.add_argument("--name", type=str, default="mold_yolov8n",
                        help="Experiment name")
    parser.add_argument("--patience", type=int, default=5,
                        help="Early stopping patience")
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
