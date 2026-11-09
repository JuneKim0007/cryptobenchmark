"""After effective.yaml says what runs: picks exactly those items from the implementation guide, beside it, for preparation."""
import pathlib
import sys

import yaml

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3] / "lib/cryptobench"))
from cryptobench.catalogue.guide_items import guide_items  # noqa: E402

NAME = "guide.yaml"


def file_beside(effective):
    return pathlib.Path(effective).with_name(NAME)


def write(effective, capture):
    """sdkInt is what a device capture reports; a host JVM has none and takes each provider's named build."""
    runtime = yaml.safe_load(pathlib.Path(capture).read_text()).get("runtime") or {}
    document = guide_items(yaml.safe_load(pathlib.Path(effective).read_text()), runtime.get("sdkInt"))
    written = file_beside(effective)
    written.write_text(yaml.safe_dump(document, sort_keys=False))
    return written
