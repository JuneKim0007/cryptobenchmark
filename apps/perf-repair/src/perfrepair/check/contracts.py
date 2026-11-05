"""The replay's role contracts: per role's folder, the charter against its row, each call's recorded inputs against the
row's required and optional, each file its runs wrote against the row's writes."""
from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path

from .. import run_dir as rd
from ..ai.runtime.engine import journal
from ..ai.runtime.engine.outbox import OutboxError, active_outbox
from ..ai.runtime.prompt.library import PACKAGED_ORIGIN
from ..catalog.role_contracts import RoleContract, role_contracts
from ..dto.charter import read_charter
from ..dto.prompt import Charter
from ..files import read_json

READ_ERRORS = (OSError, KeyError, TypeError, ValueError)


def _schema_of(contract: RoleContract) -> dict:
    return importlib.import_module(f"perfrepair.{contract.schema}").SCHEMA


def charter_problems(contract: RoleContract, charter: Charter) -> list[str]:
    """Right prompt, schema and tools; the pinned hash unless a person overrode the prompt (recorded in `sources`)."""
    problems = [] if charter.system.name == contract.prompt else [f"prompt {charter.system.name}, the contract says {contract.prompt}"]
    problems += [] if charter.schema == _schema_of(contract) else [f"schema differs from {contract.schema}"]
    problems += [] if list(charter.tools) == list(contract.tools) else [f"tools {list(charter.tools)}, the contract says {list(contract.tools)}"]
    packaged = dict(charter.sources).get(contract.prompt, PACKAGED_ORIGIN) == PACKAGED_ORIGIN
    base = replace(charter, inputs="").fingerprint
    return problems + ([f"charter hash {base}, the contract pins {contract.charter}"] if packaged and base != contract.charter else [])


def line_problems(contract: RoleContract, n: int, line: dict) -> list[str]:
    if line.get("role") != contract.role or "inputs" not in line:
        return [f"journal line {n}: role {line.get('role')!r}, no recorded inputs for {contract.role}"]
    files = [i["file"] for i in line["inputs"]]
    problems = [f"journal line {n}: required input {p} did not reach the call" for p in contract.required_missing(files)]
    return problems + [f"journal line {n}: {f} is outside the contract" for f in files if not contract.declares(f)]


def writes_problems(contract: RoleContract, doc: dict) -> list[str]:
    return [f"wrote {f}, outside the contract" for f in doc.get("files", []) if not contract.may_write(f)]


def _folder_problems(run: Path, contract: RoleContract) -> list[str]:
    folder = run / contract.folder
    try:
        outbox = active_outbox(folder)
    except OutboxError as e:
        return [str(e)]
    if outbox.fingerprint is None:
        return []
    try:
        problems = charter_problems(contract, read_charter(read_json(outbox.directory / rd.CHARTER)))
        lines = journal.read(folder / rd.JOURNAL)
    except READ_ERRORS as e:
        return [f"does not read: {e}"]
    for n, line in enumerate(lines, 1):
        if line.get("charter") == outbox.fingerprint:
            problems += line_problems(contract, n, line)
    if (folder / rd.ROLE_WRITES).is_file():
        written = read_json(folder / rd.ROLE_WRITES)
        problems += writes_problems(contract, written) if written.get("charter") == outbox.fingerprint else []
    return problems


def check_contracts(run: Path) -> dict[str, list[str]]:
    out = {}
    for contract in role_contracts().values():
        for folder in sorted(run.glob(contract.folders_glob())):
            if folder.is_dir() and (folder / "outbox").is_dir():
                name = str(folder.relative_to(run))
                out[f"{name} contract {contract.role}"] = _folder_problems(run, contract.bind(**contract.names_of(name)))
    return out
