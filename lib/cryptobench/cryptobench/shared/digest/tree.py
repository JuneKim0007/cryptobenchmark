"""byte_digest, the sha256 of some bytes; tree_digest, one digest of files, each a line of its path under root and its byte digest."""
from __future__ import annotations

import hashlib
from pathlib import Path


def byte_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_digest(root: Path, files) -> str:
    """files in the order given; the order is part of the digest."""
    return byte_digest("\n".join(f"{path.relative_to(root).as_posix()} {byte_digest(path.read_bytes())}" for path in files).encode())
