"""lib cryptobench imports keep to RULES; relative imports and imports inside functions count; __main__ modules are the top layer; tests/ folders are not the library."""
import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
LIB = REPO / "lib/cryptobench"
RUNNER = REPO / "apps/benchmark-runner"
# a top-level name found in one of an app's import roots is that app
APPS = {
    "runner": (RUNNER, RUNNER / "energy", RUNNER / "analysis"),
    "perfrepair": (REPO / "apps/perf-repair/src",),
    "cli": (REPO / "apps/cli",),
}
REPO_WIDE = ("cryptobench", *APPS)

# (importer, what it must not import); "*" makes each package there its own importer; an importer may always import itself
RULES = (
    ("cryptobench", tuple(APPS)),
    ("cryptobench.shared", ("cryptobench.pipeline", "cryptobench.stages")),
    ("cryptobench.pipeline", ("cryptobench.stages",)),
    ("cryptobench.stages.*", ("cryptobench.stages",)),
    ("cryptobench.shared.errors", REPO_WIDE),
    ("cryptobench.shared.log", REPO_WIDE),
)
# rule names whose package has not landed yet; the step that lands one removes it here
PENDING = {"cryptobench.shared.log"}
# what cryptobench/ itself may hold; every other module lives in one of these packages
TOP_LEVEL = {"__init__.py", "shared", "pipeline", "stages"}


def _within(name, prefix):
    return name == prefix or name.startswith(prefix + ".")


def _on_disk(parts):
    path = LIB.joinpath(*parts)
    return path.is_dir() or path.with_suffix(".py").is_file()


def _label(name):
    head = name.split(".")[0]
    if head == "cryptobench":
        return name
    app = next((app for app, roots in APPS.items() for root in roots
                if (root / f"{head}.py").is_file() or (root / head).is_dir()), None)
    return app and (name if head == app else f"{app}.{name}")


def _targets(node, here, is_package):
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if node.level:
        base = here if is_package else here[:-1]
        base = base[:len(base) - node.level + 1] + (node.module.split(".") if node.module else [])
    else:
        base = node.module.split(".")
    return [".".join(base + [a.name] if _on_disk(base + [a.name]) else base) for a in node.names]


def _imports():
    for path in sorted((LIB / "cryptobench").rglob("*.py")):
        if "tests" in path.relative_to(LIB).parts:
            continue
        parts = list(path.relative_to(LIB).with_suffix("").parts)
        is_package = parts[-1] == "__init__"
        here = parts[:-1] if is_package else parts
        for node in ast.walk(ast.parse(path.read_text())):
            for target in _targets(node, here, is_package):
                label = _label(target)
                if label:
                    yield ".".join(here), label, f"{path.relative_to(REPO)}:{node.lineno}"


def _unit(module, importer):
    if not importer.endswith(".*"):
        return importer if _within(module, importer) else None
    package = importer[:-2]
    rest = module[len(package) + 1:].split(".") if module.startswith(package + ".") else []
    return f"{package}.{rest[0]}" if rest else None


def _violations(importer, banned):
    for module, target, where in _imports():
        unit = _unit(module, importer)
        top = module.split(".")[-1] == "__main__" and _within(target, "cryptobench")
        if unit and not top and not _within(target, unit) and any(_within(target, b) for b in banned):
            yield f"{where}: {module} imports {target}, but {importer} must not import {', '.join(banned)}"


def _present(name):
    return _on_disk(name.split("."))


def test_every_rule_name_exists_or_is_pending():
    names = {n.removesuffix(".*") for importer, banned in RULES for n in (importer, *banned)}
    wrong = sorted(n for n in names if _within(n, "cryptobench") and _present(n) == (n in PENDING))
    assert not wrong, f"each name must exist on disk or be in PENDING, not both: {wrong}"


@pytest.mark.parametrize("importer, banned", RULES, ids=[importer for importer, _ in RULES])
def test_imports_keep_to_the_rule(importer, banned):
    if importer.removesuffix(".*") in PENDING:
        pytest.skip(f"pending: {importer}")
    found = sorted(_violations(importer, banned))
    assert not found, "\n".join(found)


def test_no_module_imports_an_entry_point():
    found = sorted(f"{where}: {module} imports {target}" for module, target, where in _imports()
                   if target.split(".")[-1] == "__main__" and not _within(module, target.rsplit(".", 1)[0]))
    assert not found, "\n".join(found)


def test_the_top_package_holds_only_its_layers():
    found = sorted(p.name for p in (LIB / "cryptobench").iterdir() if p.name != "__pycache__" and not p.name.startswith("."))
    assert set(found) <= TOP_LEVEL, f"cryptobench/ holds {found}; only {sorted(TOP_LEVEL)}"
