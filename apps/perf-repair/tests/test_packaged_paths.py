"""Every data file a package ships has its named location in the path interface."""
from cryptobench import paths


def test_every_packaged_constant_names_a_file():
    for entry in paths.ALL_PACKAGED:
        assert entry.path.is_file(), entry


def test_package_folder_and_prompts():
    assert paths.PERFREPAIR.path.is_dir() and paths.PROMPTS.path.is_dir()
