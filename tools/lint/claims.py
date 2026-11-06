"""What a doc names that code must hold: source file paths, perfrepair.yaml keys, stop codes and other snake_case or dotted names."""
from __future__ import annotations

import posixpath
import re

from lint.markdown import BACKTICK, clean, section
from lint.paths import join, router_of
from lint.tree import ROOT, Tree

SOURCE = (".py", ".kt", ".kts", ".java", ".sh", ".gradle", ".toml")
DATA = (".md", ".yaml", ".yml", ".json", ".jsonl", ".tsv", ".txt", ".log", ".jks", ".apk", ".jar", ".html", ".png", ".svg", ".xml", ".env")
TABLE = "apps/perf-repair/src/perfrepair/inputs/table.py"
CODES = "apps/perf-repair/src/perfrepair/stop/codes.py"
MOVED = "apps/perf-repair/src/perfrepair/config/settings.py"
STOPS = "apps/perf-repair/docs/stops.md"
EXTERNAL = "tools/lint/external-names.txt"
SECTIONS = ("aiGateway", "paths", "device", "apps", "timeouts", "stops")
SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
DOTTED = re.compile(r"^[a-z][A-Za-z0-9]*(\.[a-z][A-Za-z0-9]*)+$")
TESTS = re.compile(r"(^|/)tests/|/src/test/")
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SKIP = re.compile(r"[<>*{}$|\s=()\[\],'\"]")


class Code:
    """Words, perfrepair.yaml keys and stop codes as the tracked non-markdown files hold them."""

    def __init__(self, tree: Tree):
        self.text = "\n".join(_read(p) for p in tree.files if not p.endswith(".md") and not TESTS.search(p))
        self.words = set(WORD.findall(self.text))
        self.external = {line.split(" : ")[0] for line in _read(EXTERNAL).splitlines() if " : " in line}
        table, codes = _read(TABLE), _read(CODES)
        roles = re.findall(r'RoleRow\("([^"]+)"', table)
        role_keys = re.search(r"ROLE_KEYS = \(([^)]*)\)", table).group(1)
        keys = re.findall(r'"((?:%s)\.[^"\s]+)"' % "|".join(SECTIONS), table)
        keys += re.findall(r'^    "([\w.]+)": "', _read(MOVED), re.M)
        keys += [f"{r}.{k}" for r in roles for k in re.findall(r'"(\w+)"', role_keys) + ["budget"]]
        self.defaults = dict(re.findall(r'_choice\(\s*"(\w+)",\s*(\w+)', codes))
        self.codes = set(re.findall(r'_(?:fixed|choice)\(\s*"(\w+)"', codes))
        steps = re.search(r"GUIDE_STEPS = \(([^)]*)\)", codes).group(1)
        self.codes |= {f"{s}_failed" for s in re.findall(r'"(\w+)"', steps)}
        self.keys = [k.split(".") for k in keys] + [["stops", c] for c in self.codes]

    def key(self, token: str) -> bool:
        parts = token.split(".")
        return any(len(parts) <= len(k) and all(a == b or b.startswith("<") for a, b in zip(parts, k)) for k in self.keys)

    def has(self, word: str) -> bool:
        return word in self.words or word in self.codes or word in self.external


def _read(path: str) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        return ""


def _source_path(tree: Tree, src: str, token: str) -> bool:
    """A source path resolves from the repository, the doc's router, its app, or as the end of a tracked path."""
    app = "/".join(src.split("/")[:2]) if src.startswith("apps/") else ""
    for base in ("", router_of(src), app, posixpath.dirname(src)):
        if tree.exists(join(base, token)):
            return True
    tail = "/" + token.lstrip("./")
    return any(p.endswith(tail) or p == token for p in tree.files)


def claims(tree: Tree) -> list[str]:
    code, problems = Code(tree), []
    for p in tree.md:
        if p in GENERATED_DOCS:
            continue
        for n, line in enumerate(tree.text[p].splitlines(), 1):
            for raw in BACKTICK.findall(line):
                token = clean(raw)
                if not token or SKIP.search(token) or re.match(r"^[a-z]+:", token):
                    continue
                problems += [f"{p}:{n}: {kind} {token} {why}" for kind, why in _check(tree, code, p, token)]
    return problems + stop_table(tree, code)


def stop_table(tree: Tree, code: Code) -> list[str]:
    """docs/stops.md's Codes table lists exactly stop/codes.py's codes, each with its default."""
    rows = {m.group(1): m.group(2) for m in re.finditer(r"^\| `(\w+)` \| `(\w+)` \|", section(tree.text.get(STOPS, ""), "Codes"), re.M)}
    defaults = {k: v.lower() for k, v in code.defaults.items()}
    problems = [f"{STOPS}: code {c} is not in {CODES}" for c in sorted(set(rows) - code.codes)]
    problems += [f"{STOPS}: code {c} of {CODES} has no row" for c in sorted(code.codes - set(rows)) if not c.endswith("_failed")]
    return problems + [f"{STOPS}: {c} default {rows[c]}, code says {d}" for c, d in defaults.items() if c in rows and rows[c] != d]


def _check(tree: Tree, code: Code, src: str, token: str) -> list[tuple[str, str]]:
    if token.endswith(SOURCE) and not token.startswith("."):
        if tree.resolve(src, token, False) is not None:
            return []
        return [] if _source_path(tree, src, token) or token in code.text or token in code.external else [("path", "names no tracked file")]
    if token.endswith(DATA) or "/" in token:
        return []
    if token.split(".")[0] in SECTIONS and router_of(src) == "apps/perf-repair" and DOTTED.match(token):
        return [] if code.key(token) else [("setting", "is no perfrepair.yaml key (inputs/table.py)")]
    if SNAKE.match(token):
        return [] if code.has(token) else [("name", "is in no code file")]
    if DOTTED.match(token):
        missing = [w for w in token.split(".") if not code.has(w)]
        return [("key", f"has {', '.join(missing)} in no code file")] if missing else []
    return []


GENERATED_DOCS = {"docs/shared-functions.md", "apps/perf-repair/docs/shared-functions.md", "apps/perf-repair/docs/screening-list.md"}
