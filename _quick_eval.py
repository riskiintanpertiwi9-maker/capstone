"""Evaluasi cepat checkpoint: recall deteksi vs GT dan false positive dinding bersih."""
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / ".cache"
for s in ("ultralytics", "ultralytics/Ultralytics"):
    (CACHE / s).mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE / "ultralytics"))

from ultralytics import YOLO

CHECKS = {
    "ref_run@512": (BASE / "runs/detect/mold_yolov8n/weights/best.pt", 512),
    "deployed@416": (BASE / "results/yolo/train/weights/best.pt", 416),
    "finetune@416": (BASE / "results/yolo/train_v3/weights/best.pt", 416),
}
CONFS = (0.5, 0.35, 0.25)

VAL = BASE / "datasets/yolo/images/val"
LAB = BASE / "datasets/yolo/labels/val"
CLEAN = list((BASE / "datasets/trained/classifier/train/Normal Wall").glob("*")) + \
        list((BASE / "datasets/trained/classifier/val/Normal Wall").glob("*"))


def label_count(img):
    lab = LAB / f"{img.stem}.txt"
    if not lab.is_file():
        return 0
    return sum(1 for line in lab.read_text().strip().splitlines() if len(line.split()) >= 5)


def main():
    imgs = [p for p in sorted(VAL.glob("*"))
            if p.suffix.lower() in (".jpg", ".jpeg", ".png")
            and not p.name.startswith("neg_")][:20]
    print(f"val images: {len(imgs)}  clean walls: {len(CLEAN)}")
    for name, (path, sz) in CHECKS.items():
        if not path.is_file():
            print(f"skip {name}: missing")
            continue
        model = YOLO(str(path))
        print(f"\n### {name}")
        for conf in CONFS:
            hit = 0
            fp_clean = 0
            for im in imgs:
                res = model.predict(str(im), conf=conf, iou=0.35, imgsz=sz, verbose=False)[0]
                n = 0 if res.boxes is None else len(res.boxes)
                if label_count(im) == 0:
                    if n:
                        hit += 1
                elif n:
                    hit += 1
            for im in CLEAN:
                res = model.predict(str(im), conf=conf, iou=0.35, imgsz=sz, verbose=False)[0]
                if res.boxes is not None and len(res.boxes):
                    fp_clean += 1
            print(f"  conf={conf}: val hit {hit}/{len(imgs)} | clean FP {fp_clean}/{len(CLEAN)}")


if __name__ == "__main__":
    main()