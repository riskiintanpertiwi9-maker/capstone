
import csv
import random
import shutil
from collections import defaultdict
from pathlib import Path

BASE = Path(r"D:\MoldGuard\datasets\classification")
CSV_FILE = BASE / "moldvision_database.csv"
RAW = BASE / "raw_images"
SEED = 42

RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
SPLITS = list(RATIOS)

# Baca CSV dan kelompokkan berdasarkan kelas + ID sampel.
groups = defaultdict(list)
missing = []

with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    required = {"filename", "class", "ID"}

    if not required.issubset(reader.fieldnames or []):
        raise ValueError(f"Kolom CSV tidak sesuai: {reader.fieldnames}")

    for row in reader:
        filename = row["filename"].strip()
        label = row["class"].strip()
        sample_id = row["ID"].strip()
        path = RAW / filename

        if not path.is_file():
            missing.append(filename)
            continue

        groups[(label, sample_id)].append((filename, path))

if missing:
    print(f"BERHENTI: {len(missing)} gambar tidak ditemukan.")
    print("Contoh:", missing[:10])
    raise SystemExit(1)

if not groups:
    raise RuntimeError("Tidak ada gambar yang cocok dengan CSV.")

# Bagi ID di setiap kelas ke train, val, test.
random.seed(SEED)
assignment = {}

for label in sorted({key[0] for key in groups}):
    ids = sorted(
        [key for key in groups if key[0] == label],
        key=lambda key: int(key[1])
    )
    random.shuffle(ids)

    n = len(ids)
    if n < 3:
        raise RuntimeError(f"Kelas {label} memiliki kurang dari 3 ID.")

    n_train = round(n * RATIOS["train"])
    n_val = round(n * RATIOS["val"])
    n_train = max(1, min(n_train, n - 2))
    n_val = max(1, min(n_val, n - n_train - 1))

    for i, key in enumerate(ids):
        if i < n_train:
            assignment[key] = "train"
        elif i < n_train + n_val:
            assignment[key] = "val"
        else:
            assignment[key] = "test"

# Pastikan semua folder tujuan kosong agar tidak tercampur.
for split in SPLITS:
    folder = BASE / split
    if folder.exists() and any(folder.iterdir()):
        raise RuntimeError(
            f"Folder {folder} masih berisi data. "
            "Pindahkan atau ganti nama folder train, val, test lama "
            "terlebih dahulu. Tidak ada file yang diubah."
        )

# Salin gambar ke pembagian baru.
counts = defaultdict(int)

for key, items in groups.items():
    label, sample_id = key
    split = assignment[key]
    destination_dir = BASE / split / label
    destination_dir.mkdir(parents=True, exist_ok=True)

    for filename, source in items:
        shutil.copy2(source, destination_dir / filename)
        counts[(split, label)] += 1

print("\n=== PEMBAGIAN DATASET SELESAI ===")
for split in SPLITS:
    total = sum(
        value for (name, _), value in counts.items()
        if name == split
    )
    print(f"{split}: {total} gambar")

print("\nJumlah ID per kelas:")
for label in sorted({key[0] for key in groups}):
    print(f"\n{label}:")
    for split in SPLITS:
        n_ids = sum(
            1 for key, assigned in assignment.items()
            if key[0] == label and assigned == split
        )
        print(f"  {split}: {n_ids} ID")

print("\nGambar asli dan CSV tidak diubah.")
