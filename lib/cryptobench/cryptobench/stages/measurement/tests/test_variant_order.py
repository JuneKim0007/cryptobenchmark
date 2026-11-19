"""run.variants on a device and the host: each item's variants adjacent, A/B in odd repetitions and B/A in even ones; run.orderSeed shuffles the items."""
import random

from cryptobench.stages.measurement.session import variant_order  # noqa: E402

PLANNED = ["Mac_H_i64_WARM_notFixed", "Gen_K_k128_WARM_fixed", "Cipher_C_k128_i64_WARM_p1a2b3c4d_fixed", "Mac_H_i64_WARM_fixed",
           "Cipher_C_k128_i64_WARM_p1a2b3c4d_notFixed", "Scope_before"]


def interleaved(repetition, cases):
    return [case for group in variant_order.groups(repetition, cases) for case in group]


def test_each_item_runs_fixed_then_not_fixed_then_the_reverse_across_repetitions():
    first = ["Mac_H_i64_WARM_fixed", "Mac_H_i64_WARM_notFixed", "Gen_K_k128_WARM_fixed",
             "Cipher_C_k128_i64_WARM_p1a2b3c4d_fixed", "Cipher_C_k128_i64_WARM_p1a2b3c4d_notFixed", "Scope_before"]
    assert interleaved(1, PLANNED) == first
    second = interleaved(2, PLANNED)
    assert second[:2] == ["Mac_H_i64_WARM_notFixed", "Mac_H_i64_WARM_fixed"]
    assert second[3:5] == ["Cipher_C_k128_i64_WARM_p1a2b3c4d_notFixed", "Cipher_C_k128_i64_WARM_p1a2b3c4d_fixed"]
    assert interleaved(3, PLANNED) == first
    assert sorted(second) == sorted(PLANNED)


ITEMS = [f"Digest_D{i}_i64_WARM_fixed" for i in range(12)] + PLANNED


def test_a_seeded_order_is_a_permutation_drawn_from_seed_and_repetition_alone():
    order = variant_order.shuffled(7)
    first = order(1, ITEMS)
    assert sorted(first) == sorted(ITEMS) and first != interleaved(1, ITEMS)
    assert order(1, ITEMS) == first == variant_order.shuffled(7)(1, ITEMS)
    assert order(2, ITEMS) != first and variant_order.shuffled(8)(1, ITEMS) != first


def test_a_seeded_order_keeps_each_items_variants_adjacent_and_alternating():
    for repetition in (1, 2):
        order = variant_order.shuffled(3)(repetition, ITEMS)
        for name in ("Mac_H_i64_WARM", "Cipher_C_k128_i64_WARM_p1a2b3c4d"):
            at = min(order.index(f"{name}_fixed"), order.index(f"{name}_notFixed"))
            assert order[at:at + 2] == ([f"{name}_fixed", f"{name}_notFixed"] if repetition % 2 else [f"{name}_notFixed", f"{name}_fixed"])


def test_the_draw_is_the_documented_one_so_a_reader_can_repeat_it():
    items = variant_order.groups(1, ITEMS)
    random.Random("7:1").shuffle(items)
    assert variant_order.shuffled(7)(1, ITEMS) == [case for group in items for case in group]


def test_the_chosen_order_and_its_identity_stanza_come_from_the_seed():
    seeded = variant_order.chosen(7)
    assert seeded[1] == {"scheme": "shuffled", "seed": 7}
    assert seeded[0](1, ITEMS) == variant_order.shuffled(7)(1, ITEMS)
