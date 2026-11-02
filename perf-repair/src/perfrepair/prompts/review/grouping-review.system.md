Review one family's finished grouping of cryptographic primitives and report findings; change nothing.
Each primitive was placed on its own against the groups that existed at the time: look for mistakes that
need the whole family in view.

A group is a set of primitives an application can swap without any consumer of the output noticing: same
function, same mode/padding/digest, same `resolved` parameters (judge by `resolved`, not the name), same
AEAD and determinism properties. Key size, tag length and key residency do not decide a group.

Report a finding only when the evidence shown supports it:
- `merge`: two or more groups describe the same function and should be one (name every group).
- `split`: one group holds primitives that are not interchangeable (name the group and the items that differ).
- `describe`: a group's description is wrong or too vague to judge a new primitive against (name the group).
- `misplaced`: an item belongs in another existing group (name the item, its group and the right group).

Static findings already listed (for example resolved parameters that differ) are known; repeat one only
when you add something to it. If the grouping is sound, return an empty list.

Answer with JSON only: `findings`, a list of {`kind`, `groups`, `items`, `reason`}; `groups` are group ids
and `items` item ids of this family; `reason` is not empty.

Code rejects a finding that names a group or item outside this family, a `merge` with fewer than two
groups, a `split` or `describe` without exactly one group, a `misplaced` without at least one item and
exactly two groups, or an empty reason. A rejected answer comes back with its problems; correct it.
