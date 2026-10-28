
from pathlib import Path
from collections import Counter

ROOT = Path(r"D:\MoldGuard\datasets\yolo")
errors = []
counts = Counter()

for split in ("train", "val", "test"):
    images_dir = ROOT / "images" / split
    labels_dir = ROOT / "labels" / split

    if not images_dir.is_dir() or not labels_dir.is_dir():
        errors.append(f"{split}: folder images atau labels tidak ditemukan.")
        continue

    images = {
        p.stem for p in images_dir.iterdir()
        if p.is_file() and p.suffix.lower() in
        (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    }
    labels = {p.stem for p in labels_dir.glob("*.txt")}

    counts[f"{split} images"] = len(images)
    counts[f"{split} labels"] = len(labels)

    for name in sorted(images - labels):
        errors.append(f"{split}: gambar tanpa label: {name}")
    for name in sorted(labels - images):
        errors.append(f"{split}: label tanpa gambar: {name}")

    for file in labels_dir.glob("*.txt"):
        for line_no, line in enumerate(
            file.read_text(encoding="utf-8-sig").splitlines(), 1
        ):
            if not line.strip():
                continue

            parts = line.split()
            try:
                values = [float(x) for x in parts]
            except ValueError:
                errors.append(f"{split}/{file.name}:{line_no} bukan angka.")
                continue

            if len(values) != 5:
                errors.append(
                    f"{split}/{file.name}:{line_no} memiliki "
                    f"{len(values)} kolom, seharusnya 5."
                )
                continue

            cls, x, y, w, h = values

            if cls != 0:
                errors.append(
                    f"{split}/{file.name}:{line_no} kelas bukan 0."
                )
            if not all(0 <= v <= 1 for v in (x, y, w, h)):
                errors.append(
                    f"{split}/{file.name}:{line_no} koordinat di luar 0–1."
                )
            if w <= 0 or h <= 0:
                errors.append(
                    f"{split}/{file.name}:{line_no} lebar/tinggi tidak valid."
                )

print("=== JUMLAH DATA ===")
for name, count in counts.items():
    print(f"{name}: {count}")

print("\n=== HASIL PEMERIKSAAN ===")
if errors:
    print(f"Ditemukan {len(errors)} masalah. Contoh maksimal 20:")
    for error in errors[:20]:
        print("-", error)
else:
    print("LULUS: pasangan gambar-label cocok dan format bbox valid.")
