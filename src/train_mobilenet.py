
"""
MoldGuard - Train MobileNetV2 Classification Model
Training dengan progres batch, validasi, dan penyimpanan model terbaik.
"""

import argparse
import os
import time
from pathlib import Path

# Root proyek: D:\capstone (dua level di atas file ini).
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Arahkan cache Torch/Matplotlib ke drive D:.
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


# Normalisasi ImageNet
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train MobileNetV2 for MoldGuard Classification"
    )
    parser.add_argument(
        "--data_dir", type=str,
        default=str(BASE_DIR / "datasets" / "classification")
    )
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--imgsz", type=int, default=224)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Bekukan backbone dan latih classifier saja"
    )
    parser.add_argument(
        "--no_pretrained",
        action="store_true",
        help="Jangan gunakan bobot ImageNet pretrained"
    )
    parser.add_argument(
        "--save_dir", type=str,
        default=str(BASE_DIR / "results" / "mobilenet")
    )
    parser.add_argument(
        "--model_out", type=str,
        default=str(BASE_DIR / "models" / "mobilenet" / "best.pth")
    )
    return parser.parse_args()


def get_transforms(imgsz):
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(imgsz),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ColorJitter(
            brightness=0.2,
            contrast=0.2,
            saturation=0.2,
            hue=0.02
        ),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])

    val_tf = transforms.Compose([
        transforms.Resize(int(imgsz * 1.14)),
        transforms.CenterCrop(imgsz),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])

    return train_tf, val_tf


def build_model(num_classes, freeze_backbone=False, pretrained=True):
    weights = (
        models.MobileNet_V2_Weights.DEFAULT if pretrained else None
    )

    print("[INFO] Memuat arsitektur MobileNetV2...", flush=True)
    model = models.mobilenet_v2(weights=weights)

    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False

    in_features = model.classifier[1].in_features

    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, num_classes),
    )

    return model


def train_one_epoch(
    model, loader, criterion, optimizer, device, epoch, total_epochs
):
    model.train()

    running_loss = 0.0
    correct = 0
    total = 0
    total_batches = len(loader)
    start_time = time.time()

    print(
        f"\n[TRAIN] Epoch {epoch}/{total_epochs} dimulai "
        f"({total_batches} batch)",
        flush=True
    )

    for batch_idx, (images, labels) in enumerate(loader, start=1):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad(set_to_none=True)

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        batch_size = images.size(0)
        running_loss += loss.item() * batch_size

        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += batch_size

        # Tampilkan progres agar terminal tidak terlihat macet.
        if (
            batch_idx == 1
            or batch_idx % 20 == 0
            or batch_idx == total_batches
        ):
            elapsed = time.time() - start_time
            print(
                f"\r[TRAIN] Epoch {epoch}/{total_epochs} | "
                f"Batch {batch_idx}/{total_batches} | "
                f"Loss {running_loss / total:.4f} | "
                f"Acc {correct / total:.4f} | "
                f"{elapsed:.0f} detik",
                end="\n",
                flush=True
            )

    epoch_loss = running_loss / total if total else 0.0
    epoch_acc = correct / total if total else 0.0

    return epoch_loss, epoch_acc


@torch.no_grad()
def validate(model, loader, criterion, device, epoch, total_epochs):
    model.eval()

    running_loss = 0.0
    correct = 0
    total = 0
    total_batches = len(loader)

    print(
        f"[VALIDASI] Epoch {epoch}/{total_epochs} dimulai...",
        flush=True
    )

    for batch_idx, (images, labels) in enumerate(loader, start=1):
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        batch_size = images.size(0)
        running_loss += loss.item() * batch_size

        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += batch_size

        if (
            batch_idx == 1
            or batch_idx % 20 == 0
            or batch_idx == total_batches
        ):
            print(
                f"\r[VALIDASI] Batch {batch_idx}/{total_batches}",
                end="\n",
                flush=True
            )

    epoch_loss = running_loss / total if total else 0.0
    epoch_acc = correct / total if total else 0.0

    return epoch_loss, epoch_acc


def plot_curves(history, save_dir):
    if not history["train_loss"]:
        print("[PERINGATAN] Belum ada data untuk membuat grafik.")
        return

    epochs = range(1, len(history["train_loss"]) + 1)

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(epochs, history["train_loss"], label="Train Loss")
    plt.plot(epochs, history["val_loss"], label="Val Loss")
    plt.title("Loss Curve")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(epochs, history["train_acc"], label="Train Accuracy")
    plt.plot(epochs, history["val_acc"], label="Val Accuracy")
    plt.title("Accuracy Curve")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()

    out_path = Path(save_dir) / "training_curves.png"
    plt.savefig(out_path, dpi=150)
    plt.close()

    print(f"[INFO] Grafik disimpan: {out_path}", flush=True)


def main():
    args = parse_args()

    if args.epochs < 1 or args.batch < 1 or args.imgsz < 1:
        raise ValueError("Epoch, batch, dan imgsz harus lebih dari 0.")

    Path(args.save_dir).mkdir(parents=True, exist_ok=True)
    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    # Batasi thread CPU agar penggunaan sumber daya lebih terkendali.
    if device.type == "cpu":
        torch.set_num_threads(min(4, os.cpu_count() or 1))

    print("=" * 60, flush=True)
    print(" MoldGuard - MobileNetV2 Classification Training", flush=True)
    print("=" * 60, flush=True)
    print(f"[INFO] Device       : {device}", flush=True)
    print(f"[INFO] Dataset      : {args.data_dir}", flush=True)
    print(f"[INFO] Epochs       : {args.epochs}", flush=True)
    print(f"[INFO] Batch size   : {args.batch}", flush=True)
    print(f"[INFO] Image size   : {args.imgsz}", flush=True)
    print(f"[INFO] Learning rate: {args.lr}", flush=True)
    print(f"[INFO] Freeze       : {args.freeze}", flush=True)
    print(f"[INFO] Pretrained   : {not args.no_pretrained}", flush=True)
    print("=" * 60, flush=True)

    train_path = Path(args.data_dir) / "train"
    val_path = Path(args.data_dir) / "val"

    if not train_path.is_dir():
        raise FileNotFoundError(
            f"Folder train tidak ditemukan: {train_path}"
        )

    if not val_path.is_dir():
        raise FileNotFoundError(
            f"Folder val tidak ditemukan: {val_path}"
        )

    train_tf, val_tf = get_transforms(args.imgsz)

    print("[INFO] Membaca dataset...", flush=True)
    train_ds = datasets.ImageFolder(train_path, transform=train_tf)
    val_ds = datasets.ImageFolder(val_path, transform=val_tf)

    if train_ds.classes != val_ds.classes:
        raise ValueError(
            "Kelas pada train dan val tidak sama.\n"
            f"Train: {train_ds.classes}\n"
            f"Val  : {val_ds.classes}"
        )

    if len(train_ds) == 0 or len(val_ds) == 0:
        raise ValueError("Dataset train atau val kosong.")

    print(f"[INFO] Data train : {len(train_ds)}", flush=True)
    print(f"[INFO] Data val   : {len(val_ds)}", flush=True)
    print(f"[INFO] Kelas      : {train_ds.classes}", flush=True)
    print(f"[INFO] class_to_idx: {train_ds.class_to_idx}", flush=True)

    loader_options = {
        "num_workers": args.workers,
        "pin_memory": device.type == "cuda",
    }

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch,
        shuffle=True,
        **loader_options
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch,
        shuffle=False,
        **loader_options
    )

    model = build_model(
        num_classes=len(train_ds.classes),
        freeze_backbone=args.freeze,
        pretrained=not args.no_pretrained
    ).to(device)

    criterion = nn.CrossEntropyLoss()

    trainable_params = [
        p for p in model.parameters() if p.requires_grad
    ]

    optimizer = optim.AdamW(
        trainable_params,
        lr=args.lr,
        weight_decay=1e-4
    )

    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.epochs
    )

    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
    }

    best_val_acc = -1.0

    try:
        for epoch in range(1, args.epochs + 1):
            train_loss, train_acc = train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device,
                epoch,
                args.epochs
            )

            val_loss, val_acc = validate(
                model,
                val_loader,
                criterion,
                device,
                epoch,
                args.epochs
            )

            scheduler.step()

            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)

            print("\n" + "-" * 60, flush=True)
            print(
                f"Epoch [{epoch}/{args.epochs}] | "
                f"Train Loss: {train_loss:.4f} | "
                f"Train Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss:.4f} | "
                f"Val Acc: {val_acc:.4f}",
                flush=True
            )

            if val_acc > best_val_acc:
                best_val_acc = val_acc

                checkpoint = {
                    "epoch": epoch,
                    "state_dict": model.state_dict(),
                    "val_acc": val_acc,
                    "classes": train_ds.classes,
                    "class_to_idx": train_ds.class_to_idx,
                    "imgsz": args.imgsz,
                }

                torch.save(checkpoint, args.model_out)

                print(
                    f"[SIMPAN] Model terbaik: {args.model_out} "
                    f"(val_acc={val_acc:.4f})",
                    flush=True
                )

            # Simpan grafik setelah setiap epoch agar hasil sementara
            # tetap tersedia jika training dihentikan kemudian.
            plot_curves(history, args.save_dir)

    except KeyboardInterrupt:
        print(
            "\n[PERINGATAN] Training dihentikan oleh pengguna.",
            flush=True
        )
        print(
            "[INFO] Grafik yang sudah dibuat tetap tersedia. "
            "Model terbaik hanya tersedia jika sudah sempat disimpan.",
            flush=True
        )
        return

    print("=" * 60, flush=True)
    print("[INFO] Training selesai.", flush=True)
    print(f"[INFO] Best Val Acc : {best_val_acc:.4f}", flush=True)
    print(f"[INFO] Model terbaik: {args.model_out}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
