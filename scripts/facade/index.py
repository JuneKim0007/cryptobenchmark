"""The root settings file: an index of paths and of what spans a whole run; any key it does not know is an error."""
import pathlib
from dataclasses import dataclass

import yaml
from perfrepair.inputs.check import RUN_ID_FORM
from perfrepair.run_dir.run_record import ON_EXISTING, OVERWRITE

SCHEMA_VERSION = 1
SECTIONS = {"schemaVersion": None, "results": None, "run": ("id", "onExisting"), "crypto": ("config", "harnessConfig"),
            "llm": ("config",)}


class SettingsIndexError(ValueError):
    """One coded line about the index itself: nothing below it can be read."""


@dataclass(frozen=True)
class Index:
    file: pathlib.Path
    results: pathlib.Path
    crypto_config: pathlib.Path
    harness_config: pathlib.Path | None
    llm_config: pathlib.Path
    run_id: str | None
    on_existing: str


def _document(file):
    if not file.is_file():
        raise SettingsIndexError(f"missing_file: {file} (--settings)")
    try:
        document = yaml.safe_load(file.read_text())
    except yaml.YAMLError as e:
        raise SettingsIndexError(f"invalid_yaml: {file}: {' '.join(str(e).split())}") from None
    if not isinstance(document, dict):
        raise SettingsIndexError(f"invalid: {file}, a mapping of {list(SECTIONS)}")
    return document


def _check_keys(document, file):
    unknown = [key for key in document if key not in SECTIONS]
    if unknown:
        raise SettingsIndexError(f"unknown_key: {unknown} in {file}, known {list(SECTIONS)}")
    for section, keys in SECTIONS.items():
        value = document.get(section)
        if keys is None or value is None:
            continue
        if not isinstance(value, dict):
            raise SettingsIndexError(f"invalid: {section} in {file}, a mapping of {list(keys)}")
        extra = [key for key in value if key not in keys]
        if extra:
            raise SettingsIndexError(f"unknown_key: {section}.{extra} in {file}, known {list(keys)}")


def _path(value, key, file):
    if not isinstance(value, str) or not value:
        raise SettingsIndexError(f"missing_key: {key} in {file}, a path")
    return (file.parent / pathlib.Path(value).expanduser()).resolve()


def _run(document, file):
    run = document.get("run") or {}
    run_id, on_existing = run.get("id"), run.get("onExisting") or OVERWRITE
    if run_id is not None and not (isinstance(run_id, str) and RUN_ID_FORM.fullmatch(run_id)):
        raise SettingsIndexError(f"invalid: run.id {run_id} in {file}, letters, digits, '.', '_' or '-'")
    if on_existing not in ON_EXISTING:
        raise SettingsIndexError(f"invalid: run.onExisting {on_existing} in {file}, one of {list(ON_EXISTING)}")
    return run_id, on_existing


def read_index(file):
    file = pathlib.Path(file).expanduser().resolve()
    document = _document(file)
    _check_keys(document, file)
    if document.get("schemaVersion") != SCHEMA_VERSION:
        raise SettingsIndexError(f"wrong_version: {file} schemaVersion {document.get('schemaVersion')} is not {SCHEMA_VERSION}")
    crypto, llm = document.get("crypto") or {}, document.get("llm") or {}
    harness = crypto.get("harnessConfig")
    return Index(file, _path(document.get("results"), "results", file), _path(crypto.get("config"), "crypto.config", file),
                 _path(harness, "crypto.harnessConfig", file) if harness else None,
                 _path(llm.get("config"), "llm.config", file), *_run(document, file))
