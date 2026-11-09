"""charter.json: everything a charter's fingerprint hashes, and the file each prompt was read from."""
from __future__ import annotations

from cryptobench.catalogue.document import DocumentKind
from .prompt import Charter, CorrectionPrompt, SystemPrompt

SCHEMA_VERSION = 1
CHARTER_DOC = DocumentKind("charter", SCHEMA_VERSION)


def charter_document(charter: Charter) -> dict:
    sources = dict(charter.sources)

    def prompt(p) -> dict:
        return {"name": p.name, "text": p.text, "source": sources.get(p.name)}

    return {"schemaVersion": SCHEMA_VERSION, "fingerprint": charter.fingerprint, "system": prompt(charter.system),
            "schema": charter.schema, "correction": prompt(charter.correction), "inputs": charter.inputs,
            **({"tools": list(charter.tools)} if charter.tools else {})}


def read_charter(doc: dict) -> Charter:
    CHARTER_DOC.check(doc)
    system, correction = doc["system"], doc["correction"]
    return Charter(SystemPrompt(system["name"], system["text"]), doc["schema"],
                   CorrectionPrompt(correction["name"], correction["text"]), doc["inputs"],
                   tuple((p["name"], p["source"]) for p in (system, correction) if p.get("source") is not None),
                   tuple(doc.get("tools", ())))
