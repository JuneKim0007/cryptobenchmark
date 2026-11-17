"""byte_digest, the sha256 of some bytes; file_digest, of a file's bytes; tree_digest, one digest of files, each a line of its path under root and its byte digest;
globbed, the files glob patterns match but OS litter; digest_of, the tree digest of what patterns match, a pattern matching nothing refused."""
from __future__ import annotations

import hashlib
from pathlib import Path

from cryptobench.shared import paths


def byte_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path) -> str | None:
    """None when the file is absent."""
    path = Path(path)
    return byte_digest(path.read_bytes()) if path.exists() else None


def tree_digest(root: Path, files) -> str:
    """files in the order given; the order is part of the digest."""
    return byte_digest("\n".join(f"{path.relative_to(root).as_posix()} {byte_digest(path.read_bytes())}" for path in files).encode())


def globbed(root: Path, patterns) -> tuple[list[Path], list[str]]:
    """The files each pattern matches under root but OS litter, sorted per pattern, in pattern order; and the patterns that match none."""
    files, empty = [], []
    for pattern in patterns:
        matched = sorted(path for path in root.glob(pattern) if path.is_file() and not paths.litter(path))
        files += matched
        if not matched:
            empty.append(pattern)
    return files, empty


def digest_of(root: Path, patterns, refused) -> str:
    """A pattern that matches nothing is refused(`missing_file: ...`): after a move the digest would stop seeing those files."""
    files, empty = globbed(root, patterns)
    if empty:
        raise refused(f"missing_file: {empty[0]} matches nothing under {root}")
    return tree_digest(root, files)
