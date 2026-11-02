from __future__ import annotations

from ..catalog.names import Names, NamesError, fold
from ..catalog.screening import DEPRECATED, PlatformRule, Screening
from ..dto.screen import ACCEPTED, BROKEN, PLATFORM_DEPRECATED, UNKNOWN, Verdict


class ScreeningHandler:

    def __init__(self, screening: Screening, names: Names):
        self.screening, self.names = screening, names

    def verdict(self, engine_type: str, name: str, provider: str, target_sdk: int | None = None) -> Verdict:
        try:
            canonical = self.names.canonical(engine_type, name).name
        except NamesError as e:
            return Verdict(UNKNOWN, str(e))
        key = (engine_type, fold(canonical))
        crypto = self.screening.crypto.get(key)
        if crypto is not None and crypto.status == DEPRECATED:
            return Verdict(BROKEN, crypto.reason, crypto.source)
        component = self.screening.component(engine_type, canonical, self.names)
        if component is not None:
            return Verdict(BROKEN, component.reason, component.source)
        platform = self.screening.platform.get((provider, *key))
        if platform is not None and _gated(platform, target_sdk):
            return Verdict(PLATFORM_DEPRECATED, platform.reason, platform.source)
        if crypto is not None:
            return Verdict(ACCEPTED, crypto.reason, crypto.source)
        return Verdict(UNKNOWN, "no screening row")


def _gated(rule: PlatformRule, target_sdk: int | None) -> bool:
    return target_sdk is not None and target_sdk >= rule.deprecatedApi
