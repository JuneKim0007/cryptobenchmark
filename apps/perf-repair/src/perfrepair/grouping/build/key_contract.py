from __future__ import annotations

from ...catalog.key_contract import generated_key_formats, standard_key_interfaces
from ...dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN
from ...dto.signature import EXPORTABLE, NON_EXPORTABLE


def key_contract(formats: tuple[str, ...], classes: tuple[str, ...]) -> str:
    """A key format or a standard key interface: the application can hand over its key. Only other classes: a handle."""
    if formats or any(c.startswith(standard_key_interfaces()) for c in classes):
        return KEY_APP_HELD
    return KEY_PROVIDER_HELD if classes else KEY_UNKNOWN


def is_generator(engine_type: str) -> bool:
    return engine_type in generated_key_formats()


def _of_run(run: dict, standard: str) -> str:
    if not run.get("works"):
        return KEY_UNKNOWN
    if run.get("keyMaterial") == NON_EXPORTABLE:
        return KEY_PROVIDER_HELD
    return KEY_APP_HELD if run.get("keyMaterial") == EXPORTABLE and run.get("keyFormat") == standard else KEY_UNKNOWN


def produced_keys(run: dict) -> list[dict]:
    """The default run and each size the trial also asked for; a size the provider refused made no key."""
    return [run, *({**t, "works": True} for t in run.get("triedKeys") or () if not t.get("refused"))] if run else []


def generator_contract(engine_type: str, runs: list[dict]) -> str:
    """runs: the trial's, one per key size tried; a pair's private key decides. Any doubt or disagreement is unknown."""
    seen = {_of_run(r, generated_key_formats()[engine_type]) for r in runs}
    return seen.pop() if len(seen) == 1 else KEY_UNKNOWN


def cross_checked(contract: str, consumers: set[str]) -> tuple[str, str | None]:
    """The same provider's consumers of the key, by their key classes; one that says otherwise makes it unknown."""
    known = consumers - {KEY_UNKNOWN}
    if contract == KEY_UNKNOWN or not known or known == {contract}:
        return contract, None
    return KEY_UNKNOWN, (f"key_contract_conflict: the trial's key is {contract}, the provider's consumers' key classes "
                         f"say {', '.join(sorted(known))}")
