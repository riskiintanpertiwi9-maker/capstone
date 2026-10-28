"""
MoldGuard - Model Evaluation
==============================
Evaluasi performa model YOLO dan/atau MobileNet pada dataset test.

Contoh:
  python src/evaluate.py --mode yolo   --yolo_model results/yolo/train/weights/best.pt
  python src/evaluate.py --mode mobilenet --mobile_model models/mobilenet/mobilenet_mold.h5
"""

import argparse
import json
import os
from pathlib import Path

import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score, precision_score, recall_score
)


MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache"
for _sub in ("ultralytics", "ultralytics/Ultralytics", "keras", "torch", "matplotlib"):
    (CACHE_DIR / _sub).mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))
os.environ.setdefault("KERAS_HOME", str(CACHE_DIR / "keras"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))


def parse_args():
    parser = argparse.ArgumentParser(description="MoldGuard Model Evaluation")
    parser.add_argument("--mode",         type=str, default="both",                     help="yolo | mobilenet | both")
    parser.add_argument("--yolo_model",   type=str, default=str(BASE_DIR / "results" / "yolo" / "train" / "weights" / "best.pt"))
    parser.add_argument("--mobile_model", type=str, default=str(BASE_DIR / "models" / "mobilenet" / "mobilenet_mold.h5"))
    parser.add_argument("--data_yaml",    type=str, default=str(BASE_DIR / "datasets" / "trained" / "data.yaml"),  help="YOLO data config")
    parser.add_argument("--cls_test_dir", type=str, default=str(BASE_DIR / "datasets" / "trained" / "classifier" / "val"), help="Classification test dir")
    parser.add_argument("--imgsz",        type=int, default=0,                          help="MobileNet image size (0 = ikuti checkpoint)")
    parser.add_argument("--batch",        type=int, default=32)
    parser.add_argument("--save_dir",     type=str, default=str(BASE_DIR / "results"),  help="Directory to save evaluation results")
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
    from torchvision import models

    print("\n" + "=" * 50)
    print("  Evaluating MobileNetV2 Model")
    print("=" * 50)

    save_dir = Path(args.save_dir) / "mobilenet"
    save_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = Path(args.mobile_model)
    is_keras = model_path.suffix.lower() in {".h5", ".keras"}

    # Load model
    if is_keras:
        import tensorflow as tf

        keras_model = tf.keras.models.load_model(str(model_path), compile=False)
        labels_path = model_path.with_suffix(".labels.json")
        payload = json.loads(labels_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("class_names")
        classes = [str(name).strip() for name in payload]
        imgsz = args.imgsz if args.imgsz > 0 else int(keras_model.input_shape[1] or 224)
    else:
        import torch.nn as nn

        ckpt = torch.load(args.mobile_model, map_location=device)
        classes = ckpt["classes"]
        imgsz = args.imgsz if args.imgsz > 0 else int(ckpt.get("imgsz", 224))
        keras_model = models.mobilenet_v2(weights=None)
        in_features = keras_model.classifier[1].in_features
        keras_model.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, len(classes)),
        )
        keras_model.load_state_dict(ckpt["state_dict"])
        keras_model.to(device).eval()

    # Data (urutan kelas ImageFolder = alfabetis, sama dengan sidecar 9 kelas)
    if is_keras:
        tf = transforms.Compose([
            transforms.Resize((imgsz, imgsz)),
            transforms.GaussianBlur(5, sigma=0),
            transforms.ToTensor(),
        ])
    else:
        tf = transforms.Compose([
            transforms.Resize(int(imgsz * 1.14)),
            transforms.CenterCrop(imgsz),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ])
    test_ds = datasets.ImageFolder(args.cls_test_dir, transform=tf)
    if test_ds.classes != list(classes):
        raise ValueError(
            "Urutan kelas dataset tidak cocok dengan checkpoint.\n"
            f"Dataset : {test_ds.classes}\nCheckpoint: {list(classes)}"
        )
    test_dl = DataLoader(test_ds, batch_size=args.batch, shuffle=False, num_workers=0)

    all_preds, all_labels = [], []
    if is_keras:
        for imgs, labels in test_dl:
            probs = keras_model.predict(imgs.numpy(), verbose=0)
            all_preds.extend(np.argmax(probs, axis=1))
            all_labels.extend(labels.numpy())
    else:
        with torch.no_grad():
            for imgs, labels in test_dl:
                imgs = imgs.to(device)
                preds = keras_model(imgs).argmax(1).cpu().numpy()
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
