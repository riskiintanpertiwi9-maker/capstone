"""Utilitas pemetaan nama kelas classifier (satu sumber kebenaran).

Checkpoint MobileNet menyimpan urutan kelas pada dimensi output terakhir.
Urutan itu harus dipakai ulang saat inferensi; kalau tidak, nama spesies bisa
tertukar. Sidecar JSON di samping checkpoint menyimpan urutan tersebut.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


def normalize_names(names: Iterable[object]) -> List[str]:
    """Validasi dan normalisasi daftar nama kelas."""
    cleaned: List[str] = []
    for name in names:
        text = str(name).strip()
        if not text:
            raise ValueError("Nama kelas tidak boleh kosong.")
        cleaned.append(text)
    if not cleaned:
        raise ValueError("Daftar nama kelas kosong.")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("Nama kelas duplikat ditemukan.")
    return cleaned


def load_class_names(path: Path | str) -> Optional[List[str]]:
    """Baca sidecar label. Mengembalikan None bila tidak ada/tidak valid."""
    labels_path = Path(path)
    if not labels_path.is_file():
        return None
    try:
        payload = json.loads(labels_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if isinstance(payload, dict):
        payload = payload.get("class_names")
    if not isinstance(payload, list):
        return None
    try:
        return normalize_names(payload)
    except ValueError:
        return None


def save_class_names(path: Path | str, names: Sequence[str]) -> Path:
    """Tulis sidecar label secara atomik (tulis sementara lalu ganti)."""
    labels_path = Path(path)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = normalize_names(names)
    tmp_path = labels_path.with_suffix(labels_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps({"class_names": cleaned}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(labels_path)
    return labels_path


def discover_class_dirs(split_dir: Path | str) -> List[str]:
    """Ambil nama subfolder kelas (urut alfabetis) dari satu split."""
    root = Path(split_dir)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def resolve_class_names(
    labels_path: Path | str,
    discovered: Sequence[str],
) -> tuple[List[str], str]:
    """Tentukan urutan kelas final beserta sumbernya.

    Prioritas: sidecar JSON (urutan checkpoint) -> folder dataset terurut.
    """
    stored = load_class_names(labels_path)
    if stored:
        missing = [name for name in stored if name not in set(discovered)]
        if missing:
            raise ValueError(
                "Sidecar label berisi kelas yang tidak ada di dataset: "
                + ", ".join(missing)
            )
        return stored, "sidecar"
    if not discovered:
        raise ValueError("Tidak ada subfolder kelas pada dataset.")
    return sorted(discovered), "dataset"