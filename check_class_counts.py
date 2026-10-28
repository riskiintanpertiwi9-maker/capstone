
from pathlib import Path

BASE = Path(r"D:\MoldGuard\datasets\classification")
SPLITS = ["train", "val", "test"]

total_all = 0

for split in SPLITS:
    folder = BASE / split
    print(f"\n=== {split.upper()} ===")
    total_split = 0

    for class_dir in sorted(folder.iterdir()):
        if not class_dir.is_dir():
            continue

        count = sum(
            1 for p in class_dir.iterdir()
            if p.is_file() and p.suffix.lower() in
            {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        )

        print(f"{class_dir.name}: {count} gambar")
        total_split += count

    print(f"Total {split}: {total_split}")
    total_all += total_split

print(f"\nTOTAL SELURUH DATASET: {total_all} gambar")
