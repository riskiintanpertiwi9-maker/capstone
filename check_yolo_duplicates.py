
from pathlib import Path
from collections import defaultdict
import hashlib

ROOT = Path(r"D:\capstone\datasets\yolo")
SPLITS = ("train", "val", "test")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

hash_splits = defaultdict(set)
hash_files = defaultdict(list)

for split in SPLITS:
    folder = ROOT / "images" / split

    if not folder.is_dir():
        print(f"ERROR: folder tidak ditemukan: {folder}")
        raise SystemExit(1)

    for image_path in folder.iterdir():
        if not image_path.is_file() or image_path.suffix.lower() not in EXTENSIONS:
            continue

        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        hash_splits[digest].add(split)
        hash_files[digest].append((split, image_path.name))

leaks = {
    digest: files
    for digest, files in hash_files.items()
    if len(hash_splits[digest]) > 1
}

print("=== PEMERIKSAAN DUPLIKAT ANTAR-SPLIT ===")
print("Total gambar diperiksa:", sum(map(len, hash_files.values())))
print("Grup gambar identik antar-split:", len(leaks))

if leaks:
    print("\nContoh duplikat:")
    for files in list(leaks.values())[:20]:
        print(files)
    print("\nPERLU DIPERIKSA: gambar identik ditemukan di split berbeda.")
else:
    print("LULUS: tidak ditemukan gambar identik secara persis antar-split.")
