"""Ingestion: copy a file into the content store and register it.

Ingestion is idempotent by content: if a file with the same SHA-256 is already
registered, we return the existing dataset instead of storing a duplicate. This
is what lets a research org re-run an import without piling up copies.
"""
from __future__ import annotations

import datetime
import hashlib
import mimetypes
import shutil
import uuid
from pathlib import Path
from typing import Optional

from .detect import detect_kind
from .registry import Dataset, Registry


def sha256_of(path: "str | Path", chunk: int = 1 << 20) -> str:
    """Stream a file through SHA-256 so large files don't blow up memory."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def ingest_file(
    reg: Registry,
    src: "str | Path",
    store_dir: "str | Path",
    name: Optional[str] = None,
    metadata: Optional[dict] = None,
    dedup: bool = True,
) -> Dataset:
    """Register a file and copy its bytes into ``store_dir``.

    Returns the created (or, when deduplicated, the pre-existing) Dataset.
    Raises FileNotFoundError if ``src`` is not a file.
    """
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(src)

    store_dir = Path(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)

    digest = sha256_of(src)
    if dedup:
        existing = reg.find_by_sha256(digest)
        if existing is not None:
            return existing

    dataset_id = uuid.uuid4().hex[:12]
    dest = store_dir / f"{dataset_id}{src.suffix}"
    shutil.copy2(src, dest)

    ds = Dataset(
        id=dataset_id,
        name=name or src.name,
        original_filename=src.name,
        stored_path=str(dest),
        kind=detect_kind(src.name),
        content_type=mimetypes.guess_type(src.name)[0] or "application/octet-stream",
        size_bytes=src.stat().st_size,
        sha256=digest,
        created_at=_utc_now(),
        metadata=metadata or {},
    )
    return reg.add(ds)
