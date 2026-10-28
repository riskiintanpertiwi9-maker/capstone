
from pathlib import Path

ROOT = Path(r"D:\MoldGuard\datasets\yolo")
SPLITS = ["train", "val", "test"]

for split in SPLITS:
    images_dir = ROOT / "images" / split
    labels_dir = ROOT / "labels" / split

    if not images_dir.exists() or not labels_dir.exists():
        print(f"[LEWATI] Folder {split} belum lengkap.")
        continue

    kept_images = 0
    kept_boxes = 0
    removed_images = 0

    for image_path in list(images_dir.iterdir()):
        if not image_path.is_file():
            continue

        label_path = labels_dir / f"{image_path.stem}.txt"

        if not label_path.exists():
            print(f"[PERIKSA] Label tidak ditemukan: {image_path.name}")
            continue

        mold_lines = []

        for line in label_path.read_text(encoding="utf-8").splitlines():
            parts = line.split()

            if not parts:
                continue

            try:
                class_id = int(parts[0])
            except ValueError:
                raise ValueError(
                    f"Format label tidak valid: {label_path}"
                )

            # ID asli: crack=0, mold=1
            if class_id == 1:
                parts[0] = "0"
                mold_lines.append(" ".join(parts))
            elif class_id != 0:
                raise ValueError(
                    f"ID kelas tak dikenal ({class_id}) di {label_path}"
                )

        if not mold_lines:
            # Gambar hanya berisi retakan atau tidak punya anotasi jamur
            image_path.unlink()
            label_path.unlink()
            removed_images += 1
            continue

        label_path.write_text(
            "\n".join(mold_lines) + "\n",
            encoding="utf-8"
        )

        kept_images += 1
        kept_boxes += len(mold_lines)

    print(
        f"{split}: {kept_images} gambar jamur, "
        f"{kept_boxes} kotak jamur, "
        f"{removed_images} gambar tanpa jamur dihapus."
    )

print("\nSelesai. Periksa hasil sebelum training YOLOv8.")
