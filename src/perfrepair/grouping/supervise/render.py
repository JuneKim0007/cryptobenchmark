"""One family's review message: its groups with descriptions, every member, and the static findings."""
from __future__ import annotations

from pathlib import Path

SYSTEM = Path(__file__).with_name("supervisor.system.md")


def system_prompt() -> str:
    return SYSTEM.read_text()


def render(family: str, description: str, groups: list[dict], items: dict[str, dict], findings: list[dict]) -> str:
    lines = [f"FAMILY {family} — {description}", ""]
    for g in groups:
        lines.append(f"GROUP {g['id']} — {g['description']}")
        for m in g["members"]:
            entry = items[str(m)]
            _, name, provider = entry["qualified"].split("|")
            resolved = f" · resolved: {entry['resolved']}" if entry.get("resolved") else ""
            lines.append(f"  {m} · {name} · {provider}{resolved}")
    known = [f for f in findings if f["group"] in {g["id"] for g in groups}]
    lines += ["", "STATIC FINDINGS"] + ([f"  {f['kind']} {f['group']}: {f['detail']}" for f in known] or ["  (none)"])
    return "\n".join(lines)
