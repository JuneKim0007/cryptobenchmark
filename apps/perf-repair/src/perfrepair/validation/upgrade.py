"""Gate C of the upgrade decision: a reply names one of the item's aliases and a reason; the state validator: each row
against its item, and no row ever on an item screening does not accept."""
from __future__ import annotations

from ..dto.screen import ACCEPTED
from ..dto.upgrade import NEEDS_MIGRATION, SOURCES, STATUSES, UPGRADED, Upgrade, UpgradeItem
from .json_reply import parse_object


def check_reply(text: str, item: UpgradeItem) -> tuple[dict | None, list[str]]:
    """The accepted decision names the option's item: an alias only means something within one rendered message."""
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    by_alias = {o.alias: o for o in item.dossier.options}
    chosen, reason = d.get("option"), d.get("reason")
    if chosen not in by_alias:
        problems.append(f"option {chosen!r} is not one of {', '.join(by_alias)}")
    if not isinstance(reason, str) or not reason.strip():
        problems.append("reason is empty")
    return (None, problems) if problems else ({"option": by_alias[chosen].item, "reason": reason.strip()}, [])


def _row(u: Upgrade, item: UpgradeItem | None) -> list[str]:
    where = f"upgrade {u.scope}"
    problems = [f"{where}: status {u.status!r} is not one of {STATUSES}"] * (u.status not in STATUSES)
    problems += [f"{where}: source {u.source!r} is not one of {SOURCES}"] * (u.source not in SOURCES)
    problems += [f"{where}: upgraded without edits, or with needs"] * (u.status == UPGRADED and (not u.edits or bool(u.needs)))
    problems += [f"{where}: needs_migration without needs, or with edits"] * (u.status == NEEDS_MIGRATION and (not u.needs or bool(u.edits)))
    if u.option is None:
        return problems + [f"{where}: upgraded with no option"] * (u.status == UPGRADED)
    offered = {o.item: o for o in item.dossier.options} if item else {}
    if u.option not in offered:
        return problems + [f"{where}: {u.option} is not an offered option"]
    return problems + [f"{where}: {u.option} is {offered[u.option].screen}, not accepted"] * (offered[u.option].screen != ACCEPTED)


def validate_upgrades(rows: list[Upgrade], items: dict[str, UpgradeItem]) -> list[str]:
    return [p for u in rows for p in _row(u, items.get(u.scope))]
