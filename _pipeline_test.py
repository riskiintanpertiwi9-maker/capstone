"""Uji pipeline app (YOLO + veto classifier) pada dinding bersih dan gambar jamur."""
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / ".cache"
for s in ("ultralytics", "ultralytics/Ultralytics", "keras"):
    (CACHE / s).mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE / "ultralytics"))
os.environ.setdefault("KERAS_HOME", str(CACHE / "keras"))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2
import numpy as np
from ultralytics import YOLO
import tensorflow as tf

YOLO_PATH = BASE / "results/yolo/train_v3/weights/best.pt"
MOBILE_PATH = BASE / "models/mobilenet/mobilenet_mold.h5"
LABELS_PATH = BASE / "models/mobilenet/mobilenet_mold.labels.json"
IMG_SZ = 416
CONF = 0.5
IOU = 0.35
VETO = 0.55

from ultralytics.nn.autobackend import AutoBackend  # noqa: F401  (keep import cheap)


def preprocess(crop):
    r = cv2.resize(crop, (224, 224), interpolation=cv2.INTER_AREA)
    r = cv2.GaussianBlur(r, (5, 5), 0)
    return r.astype(np.float32) / 255.0


def main():
    import json
    classes = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    if isinstance(classes, dict):
        classes = classes["class_names"]
    yolo = YOLO(str(YOLO_PATH))
    clf = tf.keras.models.load_model(str(MOBILE_PATH), compile=False)

    def run(img_path):
        img = cv2.imread(str(img_path))
        res = yolo.predict(img, conf=CONF, iou=IOU, imgsz=IMG_SZ, verbose=False)[0]
        h, w = img.shape[:2]
        boxes = [] if res.boxes is None else res.boxes.xyxy.tolist()
        crops, kept = [], []
        for b in boxes:
            x1, y1, x2, y2 = [int(v) for v in b]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x2 - x1 < 5 or y2 - y1 < 5:
                continue
            if ((x2 - x1) * (y2 - y1)) / (w * h) > 0.92:
                continue
            crops.append(img[y1:y2, x1:x2])
            kept.append((x1, y1, x2, y2))
        if not crops:
            return 0, 0
        batch = np.stack([preprocess(c) for c in crops])
        probs = clf.predict(batch, verbose=0)
        after = 0
        for p in probs:
            cls = classes[int(np.argmax(p))]
            conf_p = float(np.max(p))
            if cls.lower() in ("normal wall", "clean") and conf_p >= VETO:
                continue
            after += 1
        return len(crops), after

    clean_dir = BASE / "datasets/trained/classifier"
    clean = sorted(p for p in clean_dir.rglob("*") if "Normal Wall" in str(p) and p.is_file())
    print(f"=== Dinding bersih: {len(clean)} gambar ===")
    total_before = total_after = flagged_after = 0
    for p in clean:
        before, after = run(p)
        total_before += before
        total_after += after
        if after:
            flagged_after += 1
        print(f"  {p.name}: box awal={before} setelah veto={after}")
    print(f"  TOTAL box {total_before} -> {total_after}; gambar masih terdeteksi: {flagged_after}/{len(clean)}")

    print("\n=== Gambar jamur (val) ===")
    val = [p for p in sorted((BASE / 'datasets/yolo/images/val').glob('*'))
           if p.suffix.lower() in ('.jpg', '.png')
           and not p.name.startswith('neg_')][:10]
    empty_after = 0
    for p in val:
        before, after = run(p)
        if after == 0:
            empty_after += 1
        print(f"  {p.name[:48]}: {before} -> {after}")
    print(f"  Gambar tanpa box tersisa: {empty_after}/{len(val)}")


if __name__ == "__main__":
    main()