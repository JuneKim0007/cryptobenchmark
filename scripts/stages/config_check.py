"""The parse-only check of a global.yaml and its test set before any build: the real parsers, through CheckConfigKt."""
import functools
import pathlib
import shlex

import gradle_runner
import yaml


class ConfigCheckError(Exception):
    pass


def parse_all(files):
    """One {global, testSet, bundled} per file; the first refusal is one ConfigCheckError line."""
    try:
        output = gradle_runner.output_of("jca-contract", shlex.join(map(str, files)), "CheckConfigKt")
    except gradle_runner.ToolFailed as e:
        raise ConfigCheckError(str(e)) from None
    return yaml.safe_load("\n".join(output))


# a run reads the answer before the build and again in discover; one Gradle start is enough
@functools.cache
def parsed(global_file):
    return parse_all([pathlib.Path(global_file)])[0]
