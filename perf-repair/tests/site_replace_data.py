"""Fake dossiers for the replacement decision; fake names only."""
from perfrepair.dto.site import SCHEMA_VERSION, Dossier, Estimate, Option, Scope, scope_id

APP = "demo-app"
SOURCE = "fun seal(data: ByteArray): ByteArray {\n    val c = Engine.get(\"ALG-A/MODE-X\")\n    return c.run(data)\n}"


def scope(file="src/Box.kt", line=11, function="seal", call="Engine.get", sinks=("persist",), key_source="keystore"):
    return Scope(scope_id(APP, file, function, line, call), APP, file, line, call, function, 10, 13, "TypeA",
                 "ALG-A/MODE-X", "P1", "literal", 128, 1024, sinks, key_source)


def dossier(options=None, **kw) -> Dossier:
    if options is None:
        options = (
            Option("R1", "TypeA|ALG-A/MODE-X|P2", {"ivLength": 12, "tagMode": "full"}, "pass",
                   (Estimate("timeNs", 0.62, 0.99, 40, "OP1 key 128 input 1024"),
                    Estimate("allocationCount", 0.9, 0.7, 40, "OP1 key 128 input 1024"))),
            Option("R2", "TypeA|ALG-A/MODE-X|P3", {}, "pass", (Estimate("timeNs", 0.97, 0.55, 12, "OP1 key 128 input 64"),)),
            Option("R3", "TypeA|ALG-B|P1", {}, "not_run", (Estimate("energyUj", 0.8, 0.96, 20, "OP1 key 128 input 1024"),)),
        )
    return Dossier(scope(**kw), SOURCE, "TypeA|ALG-A/MODE-X|P1", options)


def doc(*dossiers: Dossier, app=APP, no_options=()) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "app": app, "dossiers": [d.to_json() for d in dossiers],
            "noOptions": [{"scope": s, "reason": r} for s, r in no_options]}


def edit(kind, provider="", parameters=(), algorithm=""):
    return {"kind": kind, "provider": provider, "algorithm": algorithm,
            "parameters": [{"name": n, "value": v} for n, v in parameters]}


PINS = (("ivLength", "12"), ("tagMode", "full"))
GOOD_EDITS = [edit("set_provider", "P2"), edit("pin_parameters", parameters=PINS)]


def answer(decision="replace", option="R1", edits=None, risks=("persisted_data", "key_compatibility"), reason="timeNs ratio 0.62, pImprove 0.99"):
    return {"decision": decision, "option": option, "edits": GOOD_EDITS if edits is None else edits,
            "risks": list(risks), "reason": reason}


KEEP = answer("keep", "", [], [], "timeNs ratio 0.97 with pImprove 0.55 is too uncertain")
