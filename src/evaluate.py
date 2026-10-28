"""
MoldGuard - Model Evaluation
==============================
Evaluasi performa model YOLO dan/atau MobileNet pada dataset test.

Contoh:
  python src/evaluate.py --mode yolo   --yolo_model results/yolo/train/weights/best.pt
  python src/evaluate.py --mode mobilenet --mobile_model models/mobilenet/best.pth
"""

import argparse
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score, precision_score, recall_score
)


MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]


def parse_args():
    parser = argparse.ArgumentParser(description="MoldGuard Model Evaluation")
    parser.add_argument("--mode",         type=str, default="both",                     help="yolo | mobilenet | both")
    parser.add_argument("--yolo_model",   type=str, default="results/yolo/train/weights/best.pt")
    parser.add_argument("--mobile_model", type=str, default="models/mobilenet/best.pth")
    parser.add_argument("--data_yaml",    type=str, default="datasets/yolo/data.yaml",  help="YOLO data config")
    parser.add_argument("--cls_test_dir", type=str, default="datasets/classification/test", help="Classification test dir")
    parser.add_argument("--imgsz",        type=int, default=224,                        help="MobileNet image size")
    parser.add_argument("--batch",        type=int, default=32)
    parser.add_argument("--save_dir",     type=str, default="results",                  help="Directory to save evaluation results")
    parser.add_argument("--conf",         type=float, default=0.4,                      help="YOLO confidence threshold")
    return parser.parse_args()


# ── Helpers ─────────────────────────────────────────────────────────────────────
def save_confusion_matrix(cm, class_names, save_path, title="Confusion Matrix"):
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=class_names, yticklabels=class_names)
    plt.title(title); plt.ylabel("True Label"); plt.xlabel("Predicted Label")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"  [Saved] Confusion matrix: {save_path}")


def save_metrics_json(metrics: dict, save_path):
    with open(save_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  [Saved] Metrics JSON: {save_path}")


# ── YOLO Evaluation ─────────────────────────────────────────────────────────────
def evaluate_yolo(args):
    from ultralytics import YOLO
    print("\n" + "=" * 50)
    print("  Evaluating YOLOv8 Model")
    print("=" * 50)

    save_dir = Path(args.save_dir) / "yolo"
    save_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(args.yolo_model)
    metrics = model.val(data=args.data_yaml, conf=args.conf, plots=True, save_json=True)

    summary = {
        "mAP50":    float(metrics.box.map50),
        "mAP50-95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall":    float(metrics.box.mr),
    }
    print(f"\n  mAP@0.5     : {summary['mAP50']:.4f}")
    print(f"  mAP@0.5:0.95: {summary['mAP50-95']:.4f}")
    print(f"  Precision   : {summary['precision']:.4f}")
    print(f"  Recall      : {summary['recall']:.4f}")
    save_metrics_json(summary, save_dir / "metrics.json")
    return summary


# ── MobileNet Evaluation ────────────────────────────────────────────────────────
def evaluate_mobilenet(args):
    import torch.nn as nn
    from torchvision import models

    print("\n" + "=" * 50)
    print("  Evaluating MobileNetV2 Model")
    print("=" * 50)

    save_dir = Path(args.save_dir) / "mobilenet"
    save_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load model
    ckpt = torch.load(args.mobile_model, map_location=device)
    classes = ckpt["classes"]
    num_classes = len(classes)

    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, num_classes),
    )
    model.load_state_dict(ckpt["state_dict"])
    model.to(device).eval()

    # Data
    tf = transforms.Compose([
        transforms.Resize(int(args.imgsz * 1.14)),
        transforms.CenterCrop(args.imgsz),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    test_ds = datasets.ImageFolder(args.cls_test_dir, transform=tf)
    test_dl = DataLoader(test_ds, batch_size=args.batch, shuffle=False, num_workers=2)

    all_preds, all_labels = [], []
    with torch.no_grad():
        for imgs, labels in test_dl:
            imgs = imgs.to(device)
            preds = model(imgs).argmax(1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())

    all_preds  = np.array(all_preds)
    all_labels = np.array(all_labels)

    acc  = accuracy_score(all_labels, all_preds)
    f1   = f1_score(all_labels, all_preds, average="weighted")
    prec = precision_score(all_labels, all_preds, average="weighted")
    rec  = recall_score(all_labels, all_preds, average="weighted")

    print(f"\n  Accuracy  : {acc:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1-Score  : {f1:.4f}")
    print(f"\n{classification_report(all_labels, all_preds, target_names=classes)}")

    cm = confusion_matrix(all_labels, all_preds)
    save_confusion_matrix(cm, classes, save_dir / "confusion_matrix.png")

    summary = {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1}
    save_metrics_json(summary, save_dir / "metrics.json")
    return summary


def main():
    args = parse_args()
    results = {}
    if args.mode in ("yolo", "both"):
        results["yolo"] = evaluate_yolo(args)
    if args.mode in ("mobilenet", "both"):
        results["mobilenet"] = evaluate_mobilenet(args)

    print("\n" + "=" * 50)
    print("  Evaluation Summary")
    print("=" * 50)
    for model_name, metrics in results.items():
        print(f"\n  [{model_name.upper()}]")
        for k, v in metrics.items():
            print(f"    {k:20s}: {v:.4f}")


if __name__ == "__main__":
    main()
