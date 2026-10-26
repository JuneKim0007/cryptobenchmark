from __future__ import annotations

from ...dto.grouping import parse_qualified

def render(family: str, description: str, groups: list[dict], items: dict[str, dict], findings: list[dict]) -> str:
    lines = [f"FAMILY {family} — {description}", ""]
    for g in groups:
        lines.append(f"GROUP {g['id']} — {g['description']}")
        for m in g["members"]:
            entry = items[str(m)]
            _, name, provider = parse_qualified(entry["qualified"])
            resolved = f" · resolved: {entry['resolved']}" if entry.get("resolved") else ""
            lines.append(f"  {m} · {name} · {provider}{resolved}")
    known = [f for f in findings if f["group"] in {g["id"] for g in groups}]
    lines += ["", "STATIC FINDINGS"] + ([f"  {f['kind']} {f['group']}: {f['detail']}" for f in known] or ["  (none)"])
    return "\n".join(lines)
