"""run.variants on a device: each item's variants adjacent, A/B in odd repetitions and B/A in even ones."""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from session import variant_order  # noqa: E402

PLANNED = ["Mac_H_i64_WARM_notFixed", "Gen_K_k128_WARM_fixed", "Cipher_C_k128_i64_WARM_p1a2b3c4d_fixed", "Mac_H_i64_WARM_fixed",
           "Cipher_C_k128_i64_WARM_p1a2b3c4d_notFixed", "Scope_before"]


def test_each_item_runs_fixed_then_not_fixed_then_the_reverse_across_repetitions():
    first = ["Mac_H_i64_WARM_fixed", "Mac_H_i64_WARM_notFixed", "Gen_K_k128_WARM_fixed",
             "Cipher_C_k128_i64_WARM_p1a2b3c4d_fixed", "Cipher_C_k128_i64_WARM_p1a2b3c4d_notFixed", "Scope_before"]
    assert variant_order.interleaved(1, PLANNED) == first
    second = variant_order.interleaved(2, PLANNED)
    assert second[:2] == ["Mac_H_i64_WARM_notFixed", "Mac_H_i64_WARM_fixed"]
    assert second[3:5] == ["Cipher_C_k128_i64_WARM_p1a2b3c4d_notFixed", "Cipher_C_k128_i64_WARM_p1a2b3c4d_fixed"]
    assert variant_order.interleaved(3, PLANNED) == first
    assert sorted(second) == sorted(PLANNED)


def test_the_item_is_the_id_without_its_variant():
    assert variant_order.item("A_WARM_notFixed") == "A_WARM"
    assert variant_order.item("A_WARM") == "A_WARM"
    assert variant_order.item("fixed") == "fixed"
