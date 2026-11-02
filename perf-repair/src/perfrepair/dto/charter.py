"""charter.json: everything a charter's fingerprint hashes, and the file each prompt was read from."""
from __future__ import annotations

from .prompt import Charter, CorrectionPrompt, SystemPrompt

SCHEMA_VERSION = 1


def charter_document(charter: Charter) -> dict:
    sources = dict(charter.sources)

    def prompt(p) -> dict:
        return {"name": p.name, "text": p.text, "source": sources.get(p.name)}

    return {"schemaVersion": SCHEMA_VERSION, "fingerprint": charter.fingerprint, "system": prompt(charter.system),
            "schema": charter.schema, "correction": prompt(charter.correction), "inputs": charter.inputs}


def read_charter(doc: dict) -> Charter:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"charter schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
    system, correction = doc["system"], doc["correction"]
    return Charter(SystemPrompt(system["name"], system["text"]), doc["schema"],
                   CorrectionPrompt(correction["name"], correction["text"]), doc["inputs"],
                   tuple((p["name"], p["source"]) for p in (system, correction) if p.get("source") is not None))
