"""Which rails the energy sum reads: rails of the catalog's subsystems are set apart, every other rail is summed by its raw name."""
import functools, importlib.resources
from typing import NamedTuple

import yaml

CATALOG = importlib.resources.files(__package__).joinpath("excluded.yaml")


class Rails(NamedTuple):
    summed: dict
    excluded: dict
    subsystems: dict


class Unidentified(ValueError):
    pass


@functools.cache
def excluded_subsystems(path=CATALOG):
    try:
        listed = (yaml.safe_load(path.read_text()) or {}).get("subsystems")
    except (OSError, yaml.YAMLError, AttributeError) as error:
        raise SystemExit(f"rails_catalog: {path}: {type(error).__name__}") from None
    if not isinstance(listed, list) or not all(isinstance(s, str) for s in listed):
        raise SystemExit(f"rails_catalog: {path}: subsystems is not a list of names")
    return frozenset(listed)


def split(tracks, excluded):
    """tracks: {(track name, raw name, subsystem): samples}."""
    out = Rails({}, {}, {})
    for (track, raw, subsystem), samples in tracks.items():
        if not raw or raw in out.summed or raw in out.excluded:
            raise Unidentified(f"rail_unidentified: {track}: raw_name {raw!r} missing or repeated")
        (out.excluded if subsystem in excluded else out.summed)[raw] = samples
        out.subsystems[raw] = subsystem
    return out
