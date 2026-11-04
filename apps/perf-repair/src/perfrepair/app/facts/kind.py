"""What an Android tree is, from its build files and manifests alone: app, library, unknown_layout or not_android."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ...source.brackets import matching
from ...source.language import of_build_file
from ...source.lexer import mask
from ..find.sources import walk
from .roots import ANT_PROPERTIES, BUILD_FILES, MANIFEST, is_legacy
from .versions import catalog_table

APP, LIBRARY, UNKNOWN_LAYOUT, NOT_ANDROID = "app", "library", "unknown_layout", "not_android"
LEGACY_ANT, CONVENTION_PLUGIN = "legacy_ant", "convention_plugin_unresolved"
MANIFEST_ONLY, NO_ANDROID_PLUGIN = "manifest_only", "no_android_plugin"
APPLICATION_PLUGIN, LIBRARY_PLUGIN = "com.android.application", "com.android.library"
CATALOG = Path("gradle") / "libs.versions.toml"

_PLUGINS = re.compile(r"\bplugins\s*\{")
_ID = re.compile(r"""\bid\s*\(?\s*["']([\w.\-]+)["']""")
_ALIAS = re.compile(r"""\balias\s*\(\s*libs\.plugins\.([\w.]+)\s*\)""")
_APPLY = re.compile(r"""\bapply\s+plugin\s*:\s*["']([\w.\-]+)["']""")
_CATALOG_ID = re.compile(r"""^["']([\w.\-]+)(?::[^"']*)?["']|\bid\s*=\s*["']([\w.\-]+)["']""")
_APPLICATION_ID = re.compile(r"""\bapplicationId\s*(?:=\s*)?["']([^"']+)["']""")
_PACKAGE = re.compile(r"""<manifest\b[^>]*?\bpackage\s*=\s*["']([^"']+)["']""", re.DOTALL)
_ANT_LIBRARY = re.compile(r"^\s*android\.library\s*=\s*true\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Kind:
    kind: str
    reason: str | None = None
    applicationId: str | None = None


def _catalog_plugins(folder: Path) -> dict[str, str]:
    """[plugins] alias as its `libs.plugins.` accessor → plugin id; '-' and '_' read as '.', as Gradle's accessors do."""
    path = folder / CATALOG
    if not path.is_file():
        return {}
    out = {}
    for key, value in catalog_table(path.read_text(errors="replace"), "plugins").items():
        m = _CATALOG_ID.search(value)
        if m:
            out[re.sub(r"[-_]", ".", key)] = m.group(1) or m.group(2)
    return out


def _plugin_ids(text: str, name: str, catalog: dict[str, str]) -> tuple[set[str], bool]:
    """The plugin ids a build file applies, and whether its plugins {} block names one this cannot resolve."""
    language = of_build_file(name)
    code, blank = mask(text, language, strings=False), mask(text, language)
    ids = set(_APPLY.findall(code))
    named = set()
    for m in _PLUGINS.finditer(blank):
        close = matching(blank, m.end() - 1)
        block = code[m.end():close] if close else code[m.end():]
        named |= set(_ID.findall(block))
        named |= {catalog.get(alias, f"libs.plugins.{alias}") for alias in _ALIAS.findall(block)}
    return ids | named, bool(named - {APPLICATION_PLUGIN, LIBRARY_PLUGIN})


def _manifest_package(module: Path) -> str | None:
    for path in (module / MANIFEST, module / "src" / "main" / MANIFEST):
        m = _PACKAGE.search(path.read_text(errors="replace")) if path.is_file() else None
        if m:
            return m.group(1)
    return None


def _application_id(build: Path) -> str | None:
    m = _APPLICATION_ID.search(mask(build.read_text(errors="replace"), of_build_file(build.name), strings=False))
    return m.group(1) if m else _manifest_package(build.parent)


def _legacy(folder: Path) -> Kind:
    library = _ANT_LIBRARY.search((folder / ANT_PROPERTIES).read_text(errors="replace"))
    return Kind(LIBRARY if library else APP, LEGACY_ANT, _manifest_package(folder))


def _gradle(folder: Path, builds: list[Path]) -> Kind | None:
    catalog = _catalog_plugins(folder)
    applied = {p: _plugin_ids(p.read_text(errors="replace"), p.name, catalog) for p in builds}
    apps = [p for p, (ids, _) in applied.items() if APPLICATION_PLUGIN in ids]
    if apps:
        return Kind(APP, applicationId=_application_id(apps[0]))
    if any(LIBRARY_PLUGIN in ids for ids, _ in applied.values()):
        return Kind(LIBRARY)
    return Kind(UNKNOWN_LAYOUT, CONVENTION_PLUGIN) if any(u for _, u in applied.values()) else None


def android_kind(folder: Path) -> Kind:
    """Static only: an application plugin in any module makes the tree an app; nothing here builds or runs it."""
    folder = Path(folder)
    files = list(walk(folder)) if folder.is_dir() else []
    builds = [p for p in files if p.name in BUILD_FILES]
    if builds:
        found = _gradle(folder, builds)
        if found:
            return found
    elif is_legacy(folder):
        return _legacy(folder)
    if not any(p.name == MANIFEST for p in files):
        return Kind(NOT_ANDROID)
    return Kind(UNKNOWN_LAYOUT, NO_ANDROID_PLUGIN if builds else MANIFEST_ONLY)
