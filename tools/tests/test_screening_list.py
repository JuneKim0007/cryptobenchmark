import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import screening_list

DOC = {"sources": {"S": "https://example.test/s"},
       "components": {"Cipher": {"base": {"X": {"status": "deprecated", "reason": "r|x", "source": "S"}}}},
       "crypto": {"Mac": {"A": {"status": "deprecated", "reason": "weak", "source": "unsourced"},
                          "B": {"status": "accepted", "reason": "fine", "source": "S"}}}}


def test_counts_hold_every_row_and_tables_only_the_deprecated_ones():
    lines = screening_list.render(DOC).splitlines()
    assert "| Mac | 1 | 1 |" in lines
    assert "| `A` | weak | unsourced |" in lines and not any(line.startswith("| `B`") for line in lines)


def test_a_rule_links_its_source_and_escapes_a_pipe():
    assert "| `X` | r\\|x | [S](https://example.test/s) |" in screening_list.render(DOC).splitlines()
