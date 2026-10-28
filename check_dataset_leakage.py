
from collections import defaultdict
from pathlib import Path
import csv

BASE = Path(r"D:\MoldGuard\datasets\classification")
CSV_FILE = BASE / "moldvision_database.csv"
RAW = BASE / "raw_images"

# Petakan setiap pasangan (kelas, ID) ke split tempat gambarnya berada.
sample_splits = defaultdict(set)
missing = []

with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        filename = row["filename"].strip()
        label = row["class"].strip()
        sample_id = row["ID"].strip()

        if not (RAW / filename).is_file():
            missing.append(filename)
            continue

        for split in ("train", "val", "test"):
            image_path = BASE / split / label / filename

            if image_path.is_file():
                sample_splits[(label, sample_id)].add(split)

leaks = {
    key: splits
    for key, splits in sample_splits.items()
    if len(splits) > 1
}

print("=== HASIL PENGECEKAN DATASET ===")
print("Jumlah sampel (kelas + ID):", len(sample_splits))
print("Gambar sumber tidak ditemukan:", len(missing))
print("Sampel yang bocor antar-split:", len(leaks))

if missing:
    print("Contoh gambar hilang:", missing[:10])

if leaks:
    for (label, sample_id), splits in list(leaks.items())[:10]:
        print(f"KEBOCORAN: kelas={label}, ID={sample_id}, split={sorted(splits)}")
else:
    print("LULUS: tidak ada kebocoran ID antar-split.")
