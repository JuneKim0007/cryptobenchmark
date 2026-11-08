"""upgrades.json's validator: each row against its item, and no row ever on an item screening does not accept."""
from __future__ import annotations

from ..dto.screen import ACCEPTED
from ..dto.upgrade import NEEDS_MIGRATION, SOURCES, STATUSES, UPGRADED, Upgrade, UpgradeItem



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
