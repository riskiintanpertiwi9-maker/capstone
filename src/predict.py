"""
MoldGuard - Predict (Inference)
=================================
Jalankan deteksi/klasifikasi jamur pada gambar, video, atau folder.

Contoh penggunaan:
  python src/predict.py --source path/gambar.jpg --mode yolo
  python src/predict.py --source path/gambar.jpg --mode mobilenet
  python src/predict.py --source datasets/yolo/images/test --mode yolo --save
"""

import argparse
import cv2
import torch
import numpy as np
from pathlib import Path
from torchvision import transforms, models
import torch.nn as nn

# ── Constants ──────────────────────────────────────────────────────────────────
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".mp4", ".avi", ".mov"}


def parse_args():
    parser = argparse.ArgumentParser(description="MoldGuard Inference")
    parser.add_argument("--source",       type=str, required=True,                        help="Path to image / folder / video")
    parser.add_argument("--mode",         type=str, default="yolo",                       help="Model mode: yolo | mobilenet | both")
    parser.add_argument("--yolo_model",   type=str, default="results/yolo/train/weights/best.pt", help="YOLO model path")
    parser.add_argument("--mobile_model", type=str, default="models/mobilenet/best.pth",  help="MobileNet model path")
    parser.add_argument("--conf",         type=float, default=0.4,                        help="YOLO confidence threshold")
    parser.add_argument("--imgsz",        type=int, default=224,                          help="MobileNet input size")
    parser.add_argument("--save",         action="store_true",                            help="Save output images")
    parser.add_argument("--save_dir",     type=str, default="results/predictions",        help="Directory to save outputs")
    parser.add_argument("--show",         action="store_true",                            help="Display results (requires display)")
    return parser.parse_args()


# ── MobileNet Loader ────────────────────────────────────────────────────────────
def load_mobilenet(model_path: str, device: torch.device):
    ckpt = torch.load(model_path, map_location=device)
    num_classes = len(ckpt["classes"])
    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, num_classes),
    )
    model.load_state_dict(ckpt["state_dict"])
    model.to(device).eval()
    return model, ckpt["classes"]


def mobilenet_predict(model, classes, img_bgr: np.ndarray, imgsz: int, device: torch.device):
    tf = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(int(imgsz * 1.14)),
        transforms.CenterCrop(imgsz),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    tensor = tf(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs  = torch.softmax(logits, dim=1)[0]
        idx    = probs.argmax().item()
    return classes[idx], float(probs[idx])


# ── YOLO Loader ─────────────────────────────────────────────────────────────────
def load_yolo(model_path: str):
    from ultralytics import YOLO
    return YOLO(model_path)


# ── Image Annotation ────────────────────────────────────────────────────────────
def annotate_mobilenet(img: np.ndarray, label: str, conf: float) -> np.ndarray:
    label_lower = label.lower()
    if label_lower == "clean":
        color = (0, 200, 0)      # hijau
    elif label_lower == "mold":
        color = (0, 0, 220)      # merah
    elif label_lower == "suspected":
        color = (0, 165, 255)    # oranye
    else:
        color = (255, 191, 0)    # biru-kuning (default aman buat kelas spesies)
    text = f"{label}: {conf:.2%}"
    # Sesuaikan lebar biar nama kelas panjang tetep kebaca
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(img, (10, 10), (10 + tw + 20, 50), color, -1)
    cv2.putText(img, text, (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return img


def process_image(path: Path, args, yolo_model=None, mobile_model=None, mobile_classes=None, device=None):
    img = cv2.imread(str(path))
    if img is None:
        print(f"[WARN] Tidak bisa membaca: {path}")
        return

    result_img = img.copy()

    if args.mode in ("yolo", "both") and yolo_model:
        results = yolo_model.predict(img, conf=args.conf, verbose=False)
        result_img = results[0].plot()

    if args.mode in ("mobilenet", "both") and mobile_model:
        label, conf = mobilenet_predict(mobile_model, mobile_classes, img, args.imgsz, device)
        result_img = annotate_mobilenet(result_img, label, conf)
        print(f"  [MobileNet] {path.name}: {label} ({conf:.2%})")

    if args.save:
        out_dir = Path(args.save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / path.name
        cv2.imwrite(str(out_path), result_img)
        print(f"  [Saved] {out_path}")

    if args.show:
        cv2.imshow("MoldGuard Prediction", result_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    yolo_model, mobile_model, mobile_classes = None, None, None

    if args.mode in ("yolo", "both"):
        print(f"[INFO] Loading YOLO model: {args.yolo_model}")
        yolo_model = load_yolo(args.yolo_model)

    if args.mode in ("mobilenet", "both"):
        print(f"[INFO] Loading MobileNet model: {args.mobile_model}")
        mobile_model, mobile_classes = load_mobilenet(args.mobile_model, device)

    source = Path(args.source)
    if source.is_dir():
        images = [p for p in source.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}]
        print(f"[INFO] Ditemukan {len(images)} gambar.")
        for img_path in images:
            process_image(img_path, args, yolo_model, mobile_model, mobile_classes, device)
    elif source.is_file():
        process_image(source, args, yolo_model, mobile_model, mobile_classes, device)
    else:
        print(f"[ERROR] Source tidak ditemukan: {source}")


if __name__ == "__main__":
    main()
