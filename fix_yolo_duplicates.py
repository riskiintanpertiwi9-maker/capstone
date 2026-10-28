
from pathlib import Path
from collections import defaultdict
import hashlib
import shutil

ROOT = Path(r"D:\MoldGuard\datasets\yolo")
QUARANTINE = Path(r"D:\MoldGuard\datasets\yolo_duplicates_quarantine")
PRIORITY = {"test": 0, "val": 1, "train": 2}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

groups = defaultdict(list)

# Kelompokkan gambar berdasarkan hash identik.
for split in ("train", "val", "test"):
    folder = ROOT / "images" / split

    if not folder.is_dir():
        raise FileNotFoundError(f"Folder tidak ditemukan: {folder}")

    for image in folder.iterdir():
        if image.is_file() and image.suffix.lower() in EXTENSIONS:
            digest = hashlib.sha256(image.read_bytes()).hexdigest()
            groups[digest].append((split, image))

# Hanya tangani grup yang sama muncul di lebih dari satu split.
moves = []
for digest, items in groups.items():
    split_names = {split for split, _ in items}
    if len(split_names) <= 1:
        continue

    # Pertahankan salinan di split dengan prioritas tertinggi.
    keeper_split = min(split_names, key=lambda s: PRIORITY[s])

    for split, image in items:
        if split == keeper_split:
            continue

        label = ROOT / "labels" / split / f"{image.stem}.txt"
        if not label.is_file():
            raise FileNotFoundError(
                f"Label pasangan tidak ditemukan: {label}. Tidak ada file dipindahkan."
            )

        moves.append((split, image, label))

# Rencanakan semua tujuan terlebih dahulu; jangan timpa file karantina.
planned = []
for split, image, label in moves:
    for kind, source in (("images", image), ("labels", label)):
        target = QUARANTINE / split / kind / source.name
        if target.exists():
            raise FileExistsError(
                f"File karantina sudah ada: {target}. Tidak ada file dipindahkan."
            )
        planned.append((source, target))

# Pindahkan gambar dan label pasangannya, bukan menghapusnya.
completed = []
try:
    for source, target in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        completed.append((source, target))
except Exception:
    # Jika terjadi kegagalan, pulihkan file yang sudah dipindahkan.
    for source, target in reversed(completed):
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(source))
    raise

print("Selesai.")
print("Pasangan gambar-label dipindahkan:", len(moves))
print("Folder karantina:", QUARANTINE)
print("Salinan yang dipertahankan: test, lalu val, lalu train.")
print("Jalankan ulang check_yolo_duplicates.py untuk verifikasi.")
