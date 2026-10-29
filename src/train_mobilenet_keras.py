"""Training / evaluasi MobileNetV2 (Keras) untuk klasifikasi crop jamur.

Ini adalah pipeline yang menghasilkan `models/mobilenet/mobilenet_mold.h5`
(checkpoint 5 kelas yang dipakai web app).

Contoh:
    python src/train_mobilenet_keras.py --data datasets/classification \
        --reset-labels --epochs 20 --batch 16 --patience 6 --name train_5class
    python src/train_mobilenet_keras.py --data datasets/classification \
        --eval-only --eval-split test

Urutan kelas mengikuti `models/mobilenet/mobilenet_mold.labels.json` agar indeks
output checkpoint tidak tertukar. Split test (jika ada) hanya untuk evaluasi.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Semua cache (Keras/TensorFlow/Matplotlib) diarahkan ke drive D:.
CACHE_DIR = PROJECT_ROOT / ".cache"
for _sub in ("keras", "matplotlib"):
    (CACHE_DIR / _sub).mkdir(parents=True, exist_ok=True)
os.environ.setdefault("KERAS_HOME", str(CACHE_DIR / "keras"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

BACKUP_DIR = PROJECT_ROOT / "results" / "backup" / "checkpoints"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MoldGuard MobileNetV2 training/evaluasi")
    parser.add_argument(
        "--data",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "classification",
        help="Folder berisi train/ val/ (dan opsional test/)",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=PROJECT_ROOT / "models" / "mobilenet" / "mobilenet_mold.labels.json",
        help="Sidecar urutan nama kelas",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "models" / "mobilenet" / "mobilenet_mold.h5",
        help="Path checkpoint hasil training",
    )
    parser.add_argument(
        "--reset-labels",
        action="store_true",
        help="Timpa sidecar label bila tidak cocok dengan folder dataset",
    )
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--unfreeze-layers",
        type=int,
        default=0,
        help="Jumlah layer terakhir backbone yang dilatih ulang (0 = frozen)",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "mobilenet",
        help="Folder log/checkpoint training",
    )
    parser.add_argument("--name", default="train_run")
    parser.add_argument(
        "--exist-ok",
        action="store_true",
        help="Izinkan memakai folder run yang sudah ada",
    )
    parser.add_argument(
        "--eval-only",
        action="store_true",
        help="Evaluasi checkpoint tanpa training",
    )
    parser.add_argument(
        "--eval-weights",
        type=Path,
        default=PROJECT_ROOT / "models" / "mobilenet" / "mobilenet_mold.h5",
        help="Checkpoint untuk --eval-only",
    )
    parser.add_argument(
        "--eval-split",
        choices=["val", "test"],
        default="val",
        help="Split evaluasi (test dipakai bila tersedia)",
    )
    return parser.parse_args()


def custom_preprocess(img: Any) -> Any:
    """Gaussian blur 5x5, sama seperti preprocessing saat training lama."""
    import cv2
    import numpy as np

    return cv2.GaussianBlur(img.astype(np.uint8), (5, 5), 0).astype(np.float32)


def build_generators(
    data_dir: Path,
    class_names: List[str],
    batch: int,
    seed: int,
    augment: bool,
) -> Tuple[Any, Any]:
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    if augment:
        train_datagen = ImageDataGenerator(
            rescale=1.0 / 255,
            preprocessing_function=custom_preprocess,
            rotation_range=15,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True,
            fill_mode="nearest",
        )
    else:
        train_datagen = ImageDataGenerator(
            rescale=1.0 / 255, preprocessing_function=custom_preprocess
        )
    eval_datagen = ImageDataGenerator(
        rescale=1.0 / 255, preprocessing_function=custom_preprocess
    )

    common = dict(
        target_size=(224, 224),
        batch_size=batch,
        class_mode="categorical",
        classes=class_names,
    )
    train_generator = train_datagen.flow_from_directory(
        data_dir / "train", shuffle=True, seed=seed, **common
    )
    val_generator = eval_datagen.flow_from_directory(
        data_dir / "val", shuffle=False, **common
    )
    return train_generator, val_generator


def evaluate(
    model: Any, generator: Any, class_names: List[str], split: str
) -> Dict[str, Any]:
    import numpy as np

    generator.reset()
    probabilities = model.predict(generator, steps=len(generator), verbose=0)
    y_true = np.asarray(generator.classes[: len(probabilities)], dtype=int)
    y_pred = np.argmax(probabilities, axis=1)

    n_classes = len(class_names)
    matrix = np.zeros((n_classes, n_classes), dtype=int)
    np.add.at(matrix, (y_true, y_pred), 1)
    total = int(matrix.sum())
    accuracy = float(np.trace(matrix) / total) if total else 0.0

    per_class: Dict[str, Dict[str, float]] = {}
    precisions: List[float] = []
    recalls: List[float] = []
    f1s: List[float] = []
    for idx, name in enumerate(class_names):
        tp = float(matrix[idx, idx])
        predicted = float(matrix[:, idx].sum())
        actual = float(matrix[idx, :].sum())
        precision = tp / predicted if predicted else 0.0
        recall = tp / actual if actual else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[name] = {
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "support": int(actual),
        }
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    return {
        "split": split,
        "samples": total,
        "accuracy": round(accuracy, 6),
        "macro_precision": round(float(np.mean(precisions)), 6) if precisions else 0.0,
        "macro_recall": round(float(np.mean(recalls)), 6) if recalls else 0.0,
        "macro_f1": round(float(np.mean(f1s)), 6) if f1s else 0.0,
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
        "class_order": class_names,
    }


def plot_confusion(matrix: List[List[int]], class_names: List[str], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    array = np.asarray(matrix)
    fig, ax = plt.subplots(figsize=(1.1 * len(class_names) + 3, 1.1 * len(class_names) + 2))
    image = ax.imshow(array, cmap="Blues")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(class_names, fontsize=8)
    ax.set_xlabel("Prediksi")
    ax.set_ylabel("Aktual")
    for row in range(array.shape[0]):
        for col in range(array.shape[1]):
            ax.text(col, row, str(array[row, col]), ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_json(payload: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def backup_if_exists(path: Path) -> None:
    if not path.is_file():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    print(f"[BACKUP] Checkpoint lama disalin ke {backup_path}")


def load_class_order(
    labels_path: Path, data_dir: Path, reset_labels: bool = False
) -> Tuple[List[str], str]:
    from utils.class_names import discover_class_dirs, load_class_names, save_class_names

    discovered = discover_class_dirs(data_dir / "train")
    if not discovered:
        raise ValueError(f"Tidak ada subfolder kelas di {data_dir / 'train'}")
    stored = load_class_names(labels_path)
    if stored:
        if set(stored) != set(discovered):
            if not reset_labels:
                raise ValueError(
                    "Sidecar label tidak cocok dengan folder dataset. "
                    f"Sidecar: {stored}. Dataset: {sorted(discovered)}. "
                    "Jalankan ulang dengan --reset-labels bila memang berganti dataset."
                )
            save_class_names(labels_path, discovered)
            print(f"[LABELS] Sidecar ditimpa mengikuti dataset: {labels_path}")
            return discovered, "dataset (reset)"
        return stored, "sidecar"
    save_class_names(labels_path, discovered)
    print(f"[LABELS] Sidecar baru dibuat: {labels_path}")
    return discovered, "dataset"


def version_info() -> Dict[str, str]:
    import tensorflow as tf

    return {"python": sys.version.split()[0], "tensorflow": tf.__version__}


def run_evaluation(args: argparse.Namespace, class_names: List[str]) -> None:
    import tensorflow as tf

    if not args.eval_weights.is_file():
        raise FileNotFoundError(f"Checkpoint evaluasi tidak ditemukan: {args.eval_weights}")
    split_dir = args.data / args.eval_split
    if not split_dir.is_dir():
        raise ValueError(
            f"Split '{args.eval_split}' tidak tersedia di {split_dir}. "
            "Evaluasi tidak dijalankan; jangan memakai data training sebagai test."
        )

    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    datagen = ImageDataGenerator(rescale=1.0 / 255, preprocessing_function=custom_preprocess)
    generator = datagen.flow_from_directory(
        split_dir,
        target_size=(224, 224),
        batch_size=args.batch,
        class_mode="categorical",
        classes=class_names,
        shuffle=False,
    )
    model = tf.keras.models.load_model(str(args.eval_weights), compile=False)
    result = evaluate(model, generator, class_names, args.eval_split)
    out_dir = args.run_dir / f"eval_{args.eval_split}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    save_json(result, out_dir / "metrics.json")
    plot_confusion(result["confusion_matrix"], class_names, out_dir / "confusion_matrix.png")
    print(f"[METRIK] split={args.eval_split} accuracy={result['accuracy']:.4f} "
          f"macro_f1={result['macro_f1']:.4f}")
    print(f"[OUTPUT] {out_dir}")


def main() -> int:
    args = parse_args()
    try:
        class_names, labels_source = load_class_order(
            args.labels, args.data, reset_labels=args.reset_labels
        )
        print(f"[KELAS] {len(class_names)} kelas (sumber: {labels_source}): {class_names}")

        if args.eval_only:
            run_evaluation(args, class_names)
            return 0

        import tensorflow as tf
        from tensorflow.keras.applications import MobileNetV2
        from tensorflow.keras.callbacks import (
            CSVLogger,
            EarlyStopping,
            ModelCheckpoint,
            ReduceLROnPlateau,
            TerminateOnNaN,
        )
        from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.optimizers import Adam

        tf.keras.utils.set_random_seed(args.seed)

        train_generator, val_generator = build_generators(
            args.data, class_names, args.batch, args.seed, augment=True
        )
        if train_generator.samples == 0 or val_generator.samples == 0:
            raise ValueError("Generator train/val kosong. Periksa struktur dataset klasifikasi.")
        print(f"[DATA] train={train_generator.samples} val={val_generator.samples}")

        base_model = MobileNetV2(
            input_shape=(224, 224, 3), include_top=False, weights="imagenet"
        )
        base_model.trainable = args.unfreeze_layers > 0
        if args.unfreeze_layers > 0:
            for layer in base_model.layers[: -args.unfreeze_layers]:
                layer.trainable = False
            print(f"[MODEL] {args.unfreeze_layers} layer terakhir backbone dilatih ulang.")

        model = Sequential(
            [
                base_model,
                GlobalAveragePooling2D(),
                Dense(128, activation="relu"),
                Dropout(0.3),
                Dense(len(class_names), activation="softmax"),
            ]
        )
        model.compile(
            optimizer=Adam(learning_rate=args.lr),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        model.summary()

        run_dir = args.run_dir / args.name
        if run_dir.exists() and not args.exist_ok:
            raise FileExistsError(
                f"Folder run sudah ada: {run_dir}. Gunakan --exist-ok atau --name lain."
            )
        run_dir.mkdir(parents=True, exist_ok=True)
        best_path = run_dir / "best.keras"
        callbacks = [
            ModelCheckpoint(
                filepath=str(best_path),
                monitor="val_accuracy",
                save_best_only=True,
                verbose=1,
            ),
            EarlyStopping(
                monitor="val_accuracy",
                patience=args.patience,
                restore_best_weights=True,
                verbose=1,
            ),
            ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=max(1, args.patience // 2),
                min_lr=1e-6,
                verbose=1,
            ),
            CSVLogger(str(run_dir / "history.csv")),
            TerminateOnNaN(),
        ]

        print(f"[TRAINING] epochs={args.epochs} batch={args.batch} lr={args.lr}")
        history = model.fit(
            train_generator,
            epochs=args.epochs,
            validation_data=val_generator,
            callbacks=callbacks,
            verbose=1,
        )
        model.save(str(run_dir / "last.keras"))
        if not best_path.is_file():
            model.save(str(best_path))

        best_model = tf.keras.models.load_model(str(best_path), compile=False)
        val_result = evaluate(best_model, val_generator, class_names, "val")
        save_json(val_result, run_dir / "metrics_val.json")
        plot_confusion(
            val_result["confusion_matrix"], class_names, run_dir / "confusion_matrix_val.png"
        )

        test_result = None
        test_dir = args.data / "test"
        if test_dir.is_dir():
            from tensorflow.keras.preprocessing.image import ImageDataGenerator
            from utils.class_names import discover_class_dirs

            test_classes = discover_class_dirs(test_dir)
            if set(test_classes) != set(class_names):
                print(
                    "[PERINGATAN] Folder test tidak cocok dengan kelas checkpoint "
                    f"({sorted(test_classes)} vs {sorted(class_names)}); evaluasi test dilewati."
                )
            else:
                test_datagen = ImageDataGenerator(
                    rescale=1.0 / 255, preprocessing_function=custom_preprocess
                )
                test_generator = test_datagen.flow_from_directory(
                    test_dir,
                    target_size=(224, 224),
                    batch_size=args.batch,
                    class_mode="categorical",
                    classes=class_names,
                    shuffle=False,
                )
                test_result = evaluate(best_model, test_generator, class_names, "test")
                save_json(test_result, run_dir / "metrics_test.json")
                plot_confusion(
                    test_result["confusion_matrix"],
                    class_names,
                    run_dir / "confusion_matrix_test.png",
                )
        else:
            print("[PERINGATAN] Split test tidak ada; evaluasi test belum dijalankan.")

        backup_if_exists(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        best_model.save(str(args.output))
        print(f"[OUTPUT] Checkpoint disimpan ke {args.output}")

        summary = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "args": {key: (str(value) if isinstance(value, Path) else value) for key, value in vars(args).items()},
            "versions": version_info(),
            "class_names": class_names,
            "best_epoch_val_accuracy": float(max(history.history.get("val_accuracy", [0]))),
            "val": val_result,
            "test": test_result,
        }
        save_json(summary, run_dir / "training_summary.json")
        print(f"[OUTPUT] Ringkasan training: {run_dir / 'training_summary.json'}")
        return 0
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())