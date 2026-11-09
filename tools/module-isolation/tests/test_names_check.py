import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from names_check import MODULE, ROOT, SOURCES, disagreements, kotlin_names, literal_violations  # noqa: E402

from cryptobench import paths  # noqa: E402

CONTRACT = paths.CONTRACT | paths.CONTRACT_PARTS


def copied_module(tmp_path: pathlib.Path) -> pathlib.Path:
    for source in MODULE.glob("*.kt"):
        (tmp_path / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def source(repo: pathlib.Path, body: str) -> None:
    path = repo / "src/Main.kt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def scanned(repo: pathlib.Path) -> set[str]:
    return literal_violations(repo, (repo / "src",), {"FileNames.EFFECTIVE": "effective.yaml", "FileNames.INTEROP_RESULT": "interop.yaml"})


def test_the_repository_agrees():
    kotlin = kotlin_names(MODULE)
    assert disagreements(kotlin, CONTRACT) == [] and literal_violations(ROOT, SOURCES, kotlin) == set()


def test_a_renamed_kotlin_file_fails(tmp_path):
    module = copied_module(tmp_path)
    names = module / "FileNames.kt"
    names.write_text(names.read_text().replace('"effective.yaml"', '"renamed.yaml"'))
    assert disagreements(kotlin_names(module), CONTRACT) == ["differs: FileNames.EFFECTIVE: kotlin renamed.yaml, python effective.yaml"]


def test_a_renamed_stamp_prefix_or_folder_fails(tmp_path):
    module = copied_module(tmp_path)
    for name, old, new in (("StampedName.kt", '"trial"', '"attempt"'), ("Folders.kt", '"preparation"', '"prepared"')):
        (module / name).write_text((module / name).read_text().replace(old, new))
    assert len(disagreements(kotlin_names(module), CONTRACT)) == 2


def test_a_name_on_one_side_only_fails(tmp_path):
    module = copied_module(tmp_path)
    names = module / "FileNames.kt"
    names.write_text(names.read_text().replace('    const val GUIDE = "guide.yaml"\n', '    const val EXTRA = "extra.yaml"\n'))
    assert disagreements(kotlin_names(module), CONTRACT) == ["kotlin only: FileNames.EXTRA = extra.yaml", "python only: FileNames.GUIDE = guide.yaml"]


def test_private_constants_are_not_names(tmp_path):
    (tmp_path / "A.kt").write_text('object A {\n    const val X = "x"\n    private const val Y = "y"\n}\n')
    assert kotlin_names(tmp_path) == {"A.X": "x"}


def test_a_name_in_any_literal_is_found(tmp_path):
    source(tmp_path, 'val a = "missing: effective.yaml"\n')
    assert scanned(tmp_path) == {"src/Main.kt: names effective.yaml"}


def test_a_longer_name_and_a_comment_pass(tmp_path):
    source(tmp_path, '// effective.yaml\nval a = "scoped-interop.yaml used-effective.yaml"\nval b = "${FileNames.EFFECTIVE}"\n')
    assert scanned(tmp_path) == set()


def test_a_file_built_from_a_literal_is_found(tmp_path):
    source(tmp_path, 'val a = File(out, "preparation")\n')
    assert len(scanned(tmp_path)) == 1


def test_a_file_named_from_values_passes(tmp_path):
    source(tmp_path, 'val a = File(folder, "${recipe.algorithm}.key")\nval b = File(out, FileNames.EFFECTIVE)\n')
    assert scanned(tmp_path) == set()
