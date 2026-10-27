"""Chooses each scope's interop check from the function shapes: round trip with a partner scope, same output, or none."""
from dataclasses import dataclass

import scope_inputs

# Producer and consumer verbs of an operation and its inverse; a scope pair matches by name with one verb swapped.
VERBS = (("encrypt", "decrypt"), ("encipher", "decipher"), ("encode", "decode"), ("seal", "unseal"), ("wrap", "unwrap"))


@dataclass(frozen=True)
class InteropPlan:
    check: str
    reason: str | None = None
    partner: str | None = None
    role: str | None = None
    index: int | None = None


def inverse(name):
    lowered = name.lower()
    for produce, consume in VERBS:
        if produce in lowered and consume not in lowered:
            at = lowered.index(produce)
            swapped = consume if name[at].islower() else consume[0].upper() + consume[1:]
            return name[:at] + swapped + name[at + len(produce):]
    return None


def only_index(parameters, type_kind):
    found = [i for i, p in enumerate(parameters) if scope_inputs.kind(p.type) == type_kind]
    return found[0] if len(found) == 1 else None


def round_trip(producer, consumer):
    returned = scope_inputs.kind(producer.returns or "")
    restored = scope_inputs.kind(consumer.returns or "")
    if returned not in scope_inputs.KOTLIN_TYPES or restored not in scope_inputs.KOTLIN_TYPES:
        return None
    artifact, plaintext = only_index(consumer.parameters, returned), only_index(producer.parameters, restored)
    if artifact is None or plaintext is None:
        return None
    return artifact, plaintext


def plan(signatures):
    """signatures: {scope id: before Signature}, in harness order."""
    by_name = {}
    for scope_id, signature in signatures.items():
        by_name.setdefault(signature.name, scope_id)
    plans = {}
    for scope_id, signature in signatures.items():
        partner = by_name.get(inverse(signature.name) or "")
        indices = round_trip(signature, signatures[partner]) if partner else None
        if indices:
            plans[scope_id] = InteropPlan("round_trip", partner=partner, role="produce", index=indices[1])
            plans.setdefault(partner, InteropPlan("round_trip", partner=scope_id, role="consume", index=indices[0]))
    for scope_id, signature in signatures.items():
        if scope_id in plans:
            continue
        if signature.returns is None:
            plans[scope_id] = InteropPlan("none", reason="no_output: the function returns nothing to compare")
        else:
            plans[scope_id] = InteropPlan("same_output")
    return plans
