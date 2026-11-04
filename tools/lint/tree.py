"""The repo's files and folders as git lists them, and the paths each guide or doc names, resolved against them."""
from __future__ import annotations

import pathlib
import posixpath
import re
import subprocess

from lint.markdown import BACKTICK, LINK, clean, map_blocks
from lint.paths import ENTRY, ROUTERS, graphed, join, local, router_of

ROOT = pathlib.Path(__file__).resolve().parents[2]


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                         cwd=ROOT, capture_output=True, check=True).stdout.decode()
    return sorted({p for p in out.split("\0") if p and (ROOT / p).is_file()})


class Tree:

    def __init__(self, files: list[str]):
        self.files = files
        self.fileset = set(files)
        self.dirs = {posixpath.dirname(p) for p in files}
        for d in list(self.dirs):
            while d:
                d = posixpath.dirname(d)
                self.dirs.add(d)
        self.md = [p for p in files if graphed(p)]
        self.text = {p: (ROOT / p).read_text(encoding="utf-8") for p in files if p.endswith(".md")}
        self.tops = {r: {(local(p) if r else p).split("/")[0] for p in files if router_of(p) == r or not r} for r in ROUTERS}

    def exists(self, path: str) -> bool:
        return path in self.fileset or path in self.dirs or (ROOT / path).exists()

    def resolve(self, src: str, token: str, link: bool) -> str | None:
        token = clean(token)
        if not token or re.search(r"[<>*{}$|\s]", token) or re.match(r"^[a-z]+:", token):
            return None
        if link:
            return join(posixpath.dirname(src), token)
        r = router_of(src)
        first = token.split("/")[0]
        if first in self.tops[r] or first == ENTRY:
            return join(r, token)
        if first == "..":
            return join(posixpath.dirname(src) if not r else r, token)
        return None

    def references(self, p: str) -> list[tuple[str, bool]]:
        refs = [(clean(t), False) for t in BACKTICK.findall(self.text[p])]
        refs += [(e, False) for b in map_blocks(p, self.text[p]) for e in b]
        refs += [(t, True) for t in LINK.findall(self.text[p])]
        return refs
