"""Bandingkan box prediksi beberapa checkpoint dengan ground truth."""
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / ".cache"
for s in ("ultralytics", "ultralytics/Ultralytics"):
    (CACHE / s).mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE / "ultralytics"))

import cv2
from ultralytics import YOLO

OUT = BASE / "_preview"
OUT.mkdir(exist_ok=True)

CHECKPOINTS = {
    "ref_run": BASE / "runs/detect/mold_yolov8n/weights/best.pt",
    "deployed": BASE / "results/yolo/train/weights/best.pt",
    "finetune": BASE / "results/yolo/train_v3/weights/best.pt",
}

VAL = BASE / "datasets/yolo/images/val"
LAB = BASE / "datasets/yolo/labels/val"


def draw(img, x1, y1, x2, y2, color, label):
    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
    cv2.putText(img, label, (int(x1) + 3, max(12, int(y1) - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)


def main():
    picks = []
    for p in sorted(VAL.glob("*")):
        if p.suffix.lower() in (".jpg", ".jpeg", ".png") and not p.name.startswith("neg_"):
            picks.append(p)
        if len(picks) >= 6:
            break

    for name, path in CHECKPOINTS.items():
        if not path.is_file():
            print(f"skip {name}: missing")
            continue
        model = YOLO(str(path))
        sizes = {512} if name == "ref_run" else {416}
        print(f"--- {name}: {path}")
        for p in picks:
            img = cv2.imread(str(p))
            h, w = img.shape[:2]
            lab = LAB / f"{p.stem}.txt"
            n_gt = 0
            if lab.is_file():
                for line in lab.read_text().strip().splitlines():
                    r = line.split()
                    if len(r) < 5:
                        continue
                    cx, cy, bw, bh = map(float, r[1:5])
                    x1 = (cx - bw / 2) * w; y1 = (cy - bh / 2) * h
                    x2 = (cx + bw / 2) * w; y2 = (cy + bh / 2) * h
                    draw(img, x1, y1, x2, y2, (255, 0, 0), "GT")
                    n_gt += 1
            for sz in sizes:
                res = model.predict(str(p), conf=0.5, iou=0.45, imgsz=sz, verbose=False)[0]
                n = 0 if res.boxes is None else len(res.boxes)
                if res.boxes is not None:
                    for b in res.boxes:
                        x1, y1, x2, y2 = b.xyxy[0].tolist()
                        draw(img, x1, y1, x2, y2, (0, 200, 0),
                             f"P {float(b.conf):.2f}")
                print(f"   {p.name}: GT={n_gt} pred={n} (imgsz={sz})")
            cv2.imwrite(str(OUT / f"{name}_{p.stem}.jpg"), img)


if __name__ == "__main__":
    main()