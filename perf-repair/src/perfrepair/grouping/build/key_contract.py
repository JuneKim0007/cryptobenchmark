from __future__ import annotations

from ...catalog.key_contract import standard_key_interfaces
from ...dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN


def key_contract(formats: tuple[str, ...], classes: tuple[str, ...]) -> str:
    """A key format or a standard key interface: the application can hand over its key. Only other classes: a handle."""
    if formats or any(c.startswith(standard_key_interfaces()) for c in classes):
        return KEY_APP_HELD
    return KEY_PROVIDER_HELD if classes else KEY_UNKNOWN
