"""Fake dossiers for the replacement decision; fake names only."""
from perfrepair.dto.lifecycle import Lifecycle, Requirement, Step
from perfrepair.dto.site import DOSSIERS_SCHEMA_VERSION, Dossier, Estimate, Option, Scope, scope_id
from perfrepair.dto.unit import Link, Unit, UnitDossiers, unit_entry, unit_id

APP = "demo-app"
SOURCE = "fun seal(data: ByteArray): ByteArray {\n    val c = Engine.get(\"ALG-A/MODE-X\")\n    return c.run(data)\n}"


LIFECYCLE = Lifecycle("partially_bounded", ("depth1",), "local",
                      (Step("use", "run", 12, "same"), Step("configure", "prepare", 20, "depth1")),
                      (Requirement("key", "field", 3, 20, ("keystore",)), Requirement("input", "parameter", 10, 12)),
                      ("OP1",))


def scope(file="src/Box.kt", line=11, function="seal", call="Engine.get", sinks=("persist",), key_source="keystore",
          lifecycle=LIFECYCLE):
    return Scope(scope_id(APP, file, function, line, call), APP, file, line, call, function, 10, 13, "TypeA",
                 "ALG-A/MODE-X", "P1", "literal", 128, 1024, sinks, key_source, lifecycle)


def dossier(options=None, **kw) -> Dossier:
    if options is None:
        options = (
            Option("R1", "TypeA|ALG-A/MODE-X|P2", {"ivLength": 12, "tagMode": "full"}, "pass",
                   (Estimate("timeNs", 0.62, 0.99, 40, "OP1 key 128 input 1024"),
                    Estimate("allocationCount", 0.9, 0.7, 40, "OP1 key 128 input 1024"))),
            Option("R2", "TypeA|ALG-A/MODE-X|P3", {}, "pass", (Estimate("timeNs", 0.97, 0.55, 12, "OP1 key 128 input 64"),)),
            Option("R3", "TypeA|ALG-B|P1", {}, "not_run", (Estimate("energyJ", 0.8, 0.96, 20, "OP1 key 128 input 1024"),)),
        )
    return Dossier(scope(**kw), SOURCE, "TypeA|ALG-A/MODE-X|P1", options)


def solo(d: Dossier) -> Unit:
    return Unit(unit_id(APP, [d.key]), (d.key,))


def linked(*dossiers: Dossier) -> Unit:
    ids = [d.key for d in dossiers]
    return Unit(unit_id(APP, ids), tuple(ids), (Link("inverse", ids[0], ids[1], (3, 20), (3, 21), "key"),))


def item(d: Dossier) -> UnitDossiers:
    return UnitDossiers(solo(d), (d,))


def doc(*dossiers: Dossier, app=APP, no_options=(), units=None) -> dict:
    grouped = units if units is not None else [solo(d) for d in dossiers]
    return {"schemaVersion": DOSSIERS_SCHEMA_VERSION, "app": app, "perfMode": "generic", "dossiers": [d.to_json() for d in dossiers],
            "noOptions": [{"scope": s, "reason": r} for s, r in no_options], "units": [u.entry() if isinstance(u, UnitDossiers) else unit_entry(u, (), ()) for u in grouped]}


def edit(kind, provider="", parameters=(), algorithm=""):
    return {"kind": kind, "provider": provider, "algorithm": algorithm,
            "parameters": [{"name": n, "value": v} for n, v in parameters]}


PINS = (("ivLength", "12"), ("tagMode", "full"))
GOOD_EDITS = [edit("set_provider", "P2"), edit("pin_parameters", parameters=PINS)]


def member(alias="S1", option="R1", edits=None, risks=("persisted_data", "key_compatibility")):
    return {"member": alias, "option": option, "edits": GOOD_EDITS if edits is None else edits, "risks": list(risks)}


def answer(decision="replace", option="R1", edits=None, risks=("persisted_data", "key_compatibility"), reason="timeNs ratio 0.62, pImprove 0.99"):
    return {"decision": decision, "members": [member("S1", option, edits, risks)], "reason": reason}


KEEP = {"decision": "keep", "members": [], "reason": "timeNs ratio 0.97 with pImprove 0.55 is too uncertain"}
