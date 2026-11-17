"""run.variants on a device: an item's fixed and notFixed cases adjacent, fixed first in odd repetitions and last in even ones (A/B/B/A);
run.orderSeed shuffles the items per process."""
import random

from cryptobench.shared.paths import VARIANTS


def item(case):
    """The case id without its variant part; an id without one is its own item."""
    head, _, last = case.rpartition("_")
    return head if head and last in VARIANTS else case


def groups(repetition, cases):
    """Items in the order the plan first names them; within one, the variants in VARIANTS order, reversed in even repetitions."""
    items = {}
    for case in cases:
        items.setdefault(item(case), []).append(case)
    rank = lambda case: VARIANTS.index(case.rpartition("_")[2]) if item(case) != case else -1
    ordered = [sorted(group, key=rank) for group in items.values()]
    return [group if repetition % 2 else group[::-1] for group in ordered]


def interleaved(repetition, cases):
    return [case for group in groups(repetition, cases) for case in group]


def shuffled(seed):
    """Items in an order drawn from (seed, repetition) alone, so a rerun repeats it; within an item, the variants as interleaved puts them."""
    def order(repetition, cases):
        drawn = groups(repetition, cases)
        random.Random(f"{seed}:{repetition}").shuffle(drawn)
        return [case for group in drawn for case in group]
    return order


def chosen(seed):
    """The order a session launches cases in, and its part of a run's identity (shared/results/identity.py)."""
    if seed is None:
        return interleaved, {"scheme": "interleaved"}
    return shuffled(seed), {"scheme": "shuffled", "seed": seed}
