"""run.variants on a device: an item's fixed and notFixed cases adjacent, fixed first in odd repetitions and last in even ones (A/B/B/A)."""
VARIANTS = ("fixed", "notFixed")   # preparation's Variant labels, the last part of a case id


def item(case):
    """The case id without its variant part; an id without one is its own item."""
    head, _, last = case.rpartition("_")
    return head if head and last in VARIANTS else case


def interleaved(repetition, cases):
    """Items in the order the plan first names them; within one, the variants in VARIANTS order, reversed in even repetitions."""
    items = {}
    for case in cases:
        items.setdefault(item(case), []).append(case)
    rank = lambda case: VARIANTS.index(case.rpartition("_")[2]) if item(case) != case else -1
    ordered = [sorted(group, key=rank) for group in items.values()]
    return [case for group in ordered for case in (group if repetition % 2 else group[::-1])]
