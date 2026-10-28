from pathlib import Path
from collections import Counter
import shutil

source = Path.home() / "Downloads" / "Wall Defects Final.v3i.yolov8"
destination = Path(r"D:\capstone\datasets\yolo")
temporary = Path(r"D:\capstone\datasets\yolo_rebuild_tmp")

if not all((source / s / sub).is_dir()
           for s in ["train", "valid", "test"]
           for sub in ["images", "labels"]):
    raise SystemExit(f"Dataset asli tidak ditemukan lengkap: {source}")

if temporary.exists():
    shutil.rmtree(temporary)

stats = Counter()
errors = []
extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

for old_split, new_split in [
    ("train", "train"), ("valid", "val"), ("test", "test")
]:
    images = source / old_split / "images"
    labels = source / old_split / "labels"
    out_images = temporary / "images" / new_split
    out_labels = temporary / "labels" / new_split
    out_images.mkdir(parents=True, exist_ok=True)
    out_labels.mkdir(parents=True, exist_ok=True)

    for label in labels.glob("*.txt"):
        image_path = next(
            (images / (label.stem + ext)
             for ext in extensions
             if (images / (label.stem + ext)).is_file()),
            None
        )
        if image_path is None:
            errors.append(f"Gambar tidak ditemukan: {label}")
            continue

        boxes = []
        for line_no, line in enumerate(
            label.read_text(encoding="utf-8").splitlines(), 1
        ):
            parts = line.split()
            if not parts:
                continue
            try:
                cls = int(parts[0])
                coords = [float(x) for x in parts[1:]]
            except ValueError:
                errors.append(f"Label tidak valid: {label.name}:{line_no}")
                continue

            if cls != 1:
                continue

            if len(coords) >= 6 and len(coords) % 2 == 0:
                xs, ys = coords[0::2], coords[1::2]
                if not all(0 <= x <= 1 for x in coords):
                    errors.append(f"Koordinat di luar 0-1: {label.name}")
                    continue
                xmin, xmax = min(xs), max(xs)
                ymin, ymax = min(ys), max(ys)
                xc, yc = (xmin + xmax) / 2, (ymin + ymax) / 2
                w, h = xmax - xmin, ymax - ymin
            elif len(coords) == 4:
                xc, yc, w, h = coords
                if not all(0 <= x <= 1 for x in coords):
                    errors.append(f"Koordinat di luar 0-1: {label.name}")
                    continue
            else:
                errors.append(f"Format tidak dikenal: {label.name}:{line_no}")
                continue

            boxes.append(f"0 {xc:.8f} {yc:.8f} {w:.8f} {h:.8f}")

        if boxes:
            shutil.copy2(image_path, out_images / image_path.name)
            (out_labels / label.name).write_text(
                "\n".join(boxes) + "\n", encoding="utf-8"
            )
            stats[f"{new_split}_images"] += 1
            stats[f"{new_split}_boxes"] += len(boxes)
        else:
            stats[f"{new_split}_skipped"] += 1

if errors:
    print("GAGAL VALIDASI. Dataset lama tidak disentuh.")
    print("\n".join(errors[:30]))
    print(f"Total kesalahan: {len(errors)}")
    raise SystemExit("Perbaiki sumber sebelum mengganti dataset kerja.")

(temporary / "data.yaml").write_text(
    "path: D:/capstone/datasets/yolo\n"
    "train: images/train\n"
    "val: images/val\n"
    "test: images/test\n"
    "nc: 1\n"
    "names: ['mold']\n",
    encoding="utf-8"
)

# Dataset kerja lama baru diganti setelah seluruh proses validasi berhasil.
backup = Path(r"D:\capstone\datasets\yolo_backup")
if backup.exists():
    raise SystemExit(
        f"Backup sudah ada: {backup}. Dataset lama tidak diganti."
    )

if destination.exists():
    destination.rename(backup)

try:
    temporary.rename(destination)
except Exception:
    if backup.exists() and not destination.exists():
        backup.rename(destination)
    raise

print("\nDATASET BERHASIL DIBUAT")
for split in ["train", "val", "test"]:
    print(
        f"{split}: {stats[split + '_images']} gambar, "
        f"{stats[split + '_boxes']} kotak jamur, "
        f"{stats[split + '_skipped']} gambar tanpa anotasi jamur dilewati"
    )
print(f"Dataset baru : {destination}")
print(f"Cadangan lama: {backup if backup.exists() else 'tidak ada'}")
