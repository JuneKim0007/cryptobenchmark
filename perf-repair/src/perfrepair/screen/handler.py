from __future__ import annotations

from dataclasses import replace

from ..catalog.names import Names, NamesError, fold
from ..catalog.screening import DEPRECATED, PlatformRule, Screening
from ..dto.grouping import parse_qualified
from ..dto.screen import ACCEPTED, BROKEN, PLATFORM_DEPRECATED, UNKNOWN, Verdict, qualified_verdicts


class ScreeningHandler:

    def __init__(self, screening: Screening, names: Names):
        self.screening, self.names = screening, names

    @classmethod
    def packaged(cls) -> "ScreeningHandler":
        # catalog names without the probe's aliases: app_verdicts reads canonical names screen.json recorded
        names = Names.load()
        return cls(Screening.load(names=names), names)

    def verdict(self, engine_type: str, name: str, provider: str, target_sdk: int | None = None) -> Verdict:
        try:
            found = self.names.canonical(engine_type, name)
        except NamesError as e:
            return Verdict(UNKNOWN, str(e))
        recorded = replace(self._screen(engine_type, found.name), canonical=found.name, keySize=found.keySize)
        return self.for_app(recorded, engine_type, provider, target_sdk)

    def for_app(self, verdict: Verdict, engine_type: str, provider: str, target_sdk: int | None) -> Verdict:
        """A run-level verdict raised to platform_deprecated when the app's targetSdk passes the provider's gate."""
        if verdict.status == BROKEN or verdict.canonical is None:
            return verdict
        platform = self.screening.platform.get((provider, engine_type, fold(verdict.canonical)))
        if platform is None or not _gated(platform, target_sdk):
            return verdict
        return replace(verdict, status=PLATFORM_DEPRECATED, reason=platform.reason, source=platform.source)

    def app_verdicts(self, groups: dict, screen: dict[int, Verdict] | None,
                     target_sdk: int | None) -> dict[str, Verdict] | None:
        """Each groups.json item's verdict for one app, by qualified name; None without screen.json."""
        run_level = qualified_verdicts(groups, screen)
        if run_level is None:
            return None
        return {q: self.for_app(v, parse_qualified(q)[0], parse_qualified(q)[2], target_sdk)
                for q, v in run_level.items()}

    def _screen(self, engine_type: str, canonical: str) -> Verdict:
        key = (engine_type, fold(canonical))
        crypto = self.screening.crypto.get(key)
        if crypto is not None and crypto.status == DEPRECATED:
            return Verdict(BROKEN, crypto.reason, crypto.source)
        component = self.screening.component(engine_type, canonical, self.names)
        if component is not None:
            return Verdict(BROKEN, component.reason, component.source)
        if crypto is not None:
            return Verdict(ACCEPTED, crypto.reason, crypto.source)
        return Verdict(UNKNOWN, "no screening row")


def _gated(rule: PlatformRule, target_sdk: int | None) -> bool:
    return target_sdk is not None and target_sdk >= rule.deprecatedApi
