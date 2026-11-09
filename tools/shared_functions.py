"""Writes the shared-functions index of each code root: the functions other modules import, with their callers; --check fails when a written index differs."""
import argparse
import ast
import collections
import pathlib
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (title, router, doc, source roots each a module search path, least importing modules a function needs to be listed)
INDEXES = [("benchmark runner, cli and tools", "", "docs/shared-functions.md",
            ["apps/benchmark-runner", "apps/benchmark-runner/energy", "apps/benchmark-runner/analysis", "apps/cli", "tools"], 2),
           ("perf-repair", "apps/perf-repair", "docs/shared-functions.md", ["src"], 3)]
GENERAL = {"apps/benchmark-runner/failure.py": {"one_line", "fail"}, "apps/benchmark-runner/device/adb.py": {"PASSED", "ONE_PASSED"},
           "apps/benchmark-runner/repo.py": {"ROOT"}, "apps/benchmark-runner/results/select.py": {"device_folders"},
           "apps/benchmark-runner/energy/energy.py": {"one_line"}, "apps/benchmark-runner/energy/manafa_estimate.py": {"one_line"},
           "src/perfrepair/run_dir/layout.py": {"device_folders"}}


def modules(roots):
    found = {}
    for root in roots:
        # a root inside another is its own search path, not a package of the outer one
        inner = [ROOT / other for other in roots if other.startswith(root + "/")]
        for path in sorted((ROOT / root).rglob("*.py")):
            relative = path.relative_to(ROOT / root)
            if "tests" in relative.parts or "build" in relative.parts or any(path.is_relative_to(i) for i in inner):
                continue
            parts = relative.with_suffix("").parts
            name = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
            # sorted, the package comes first and keeps the name, as at runtime; a script of its name has no importers
            found[f"{name}.py" if name in found else name] = path
    return found


def base_of(node, package):
    parts = package.split(".")[: len(package.split(".")) - node.level + 1] if node.level else []
    return ".".join([p for p in parts if p] + ([node.module] if node.module else []))


def from_import(node, package, found, exported, aliases, reads):
    """A package's re-export of a name wins over its submodule of that name, as at runtime."""
    base = base_of(node, package)
    for a in node.names:
        full = f"{base}.{a.name}" if base else a.name
        if (base, a.name) in exported:
            reads.add(exported[(base, a.name)])
        elif full in found:
            aliases[a.asname or a.name] = full
        elif base in found:
            reads.add((base, a.name))


def plain_import(node, found):
    return {a.asname or a.name: a.name for a in node.names if a.name in found}


def imported(path, name, found, exported):
    """(module, name) pairs this module reads, through `from m import n` and `import m` then `m.n`."""
    package = name if path.name == "__init__.py" else name.rpartition(".")[0]
    aliases, reads = {}, set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            aliases.update(plain_import(node, found))
        elif isinstance(node, ast.ImportFrom):
            from_import(node, package, found, exported, aliases, reads)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
            target = (aliases[node.value.id], node.attr)
            reads.add(exported.get(target, target))
    return reads


def rule(node):
    """The docstring's first line, else the one statement it returns or assigns."""
    doc = ast.get_docstring(node) if isinstance(node, ast.FunctionDef) else None
    if doc:
        return doc.split("\n")[0]
    body = node.body if isinstance(node, ast.FunctionDef) else [node]
    single = len(body) == 1 and isinstance(body[0], (ast.Return, ast.Assign)) and body[0].value
    return f"`{textwrap.shorten(ast.unparse(body[0].value), 110, placeholder=' ...')}`" if single else "-"


def definitions(found):
    out = {}
    for name, path in found.items():
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                args = ", ".join(a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs)
                out[(name, node.name)] = (path, f"{node.name}({args})", rule(node))
            elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                out[(name, node.targets[0].id)] = (path, node.targets[0].id, rule(node))
    return out


def exports(packages, found, defined):
    return {(name, target[1]): target for name, path in packages.items() for target in imported(path, name, found, {}) if target in defined}


def callers_of(found, defined):
    """Importing modules per definition; a package's __init__ re-exports and is no caller."""
    packages = {name: path for name, path in found.items() if path.name == "__init__.py"}
    exported = exports(packages, found, defined)
    callers = collections.defaultdict(set)
    for name, path in found.items():
        for target in () if name in packages else imported(path, name, found, exported):
            if target in defined and target[0] != name:
                callers[target].add(name.removeprefix("perfrepair."))
    return callers


def row(signature, module, text, users):
    shown = ", ".join(users[:4]) + (f" +{len(users) - 4}" if len(users) > 4 else "")
    return "| " + " | ".join(c.replace("|", "\\|") for c in (f"`{signature}`", f"`{module}`", text, shown or "none")) + " |"


def listed(key, path, signature, callers, router, least):
    return key[1] in GENERAL.get(str(path.relative_to(ROOT / router)), ()) or ("(" in signature and len(callers[key]) >= least)


def index(title, router, roots, least):
    found = modules([f"{router}/{root}".lstrip("/") for root in roots])
    defined = definitions(found)
    callers = callers_of(found, defined)
    rows = [row(signature, path.relative_to(ROOT / router), text, sorted(callers[key]))
            for key, (path, signature, text) in sorted(defined.items(), key=lambda item: (str(item[1][0]), item[1][1]))
            if listed(key, path, signature, callers, router, least)]
    return "\n".join([f"# Shared functions: {title}", "", "| function | module | rule | callers |", "|---|---|---|---|", *rows, ""])


def stale(path, text):
    return not path.is_file() or path.read_text() != text


def main(check):
    drifted = 0
    for title, router, doc, roots, least in INDEXES:
        path, text = ROOT / router / doc, index(title, router, roots, least)
        name = path.relative_to(ROOT)
        if not check:
            path.write_text(text)
            print(f"wrote:     {name}")
        elif stale(path, text):
            drifted += 1
            print(f"stale:     {name}; run python3 tools/shared_functions.py")
    return 1 if drifted else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 when an index differs from the code")
    sys.exit(main(parser.parse_args().check))
