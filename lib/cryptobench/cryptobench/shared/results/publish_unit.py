"""A verification stage's folder published from its staging: beside a finished run, its configuration kept under the stage's folder, else as a new
device folder; then the results: line, the manifest and the superseded report."""
from __future__ import annotations

import dataclasses
from typing import Callable

from cryptobench.shared import paths
from cryptobench.shared.device.identity import capture_id
from cryptobench.shared.log.stdout import RESULTS, say
from cryptobench.shared.results import layout
from cryptobench.shared.results.manifest import add_to_manifest, manifest


@dataclasses.dataclass(frozen=True)
class Route:
    # the stage's folder in the unit
    name: str
    # manifest files the stage adds, beside a finished run or not
    added: Callable[[paths.RunTree], dict]
    # manifest files only a new device folder lists
    new: Callable[[paths.RunTree], dict] = lambda _tree: {}


def publish_unit(root, stage, found, route, *, mode, configuration, discovery_mode, located, suite=None):
    """found is the staged discovery; located(results, capture name) its files once published. Returns the device folder."""
    results = layout.unit_folder(root, capture_id(found.capture), suite)
    beside = paths.finished(results)
    if beside:
        paths.RunTree(stage).configuration.root.rename(stage / route.name / paths.CONFIGURATION)
        layout.publish_beside(stage, results, route.name)
    else:
        layout.publish(stage, results, discovery_mode)
    say(RESULTS, results)
    tree = paths.RunTree(results)
    if beside:
        add_to_manifest(results, route.added(tree))
    else:
        manifest(results, mode, configuration, located(results, found.capture.name).files | route.new(tree) | route.added(tree))
    layout.report_superseded(results)
    return results
