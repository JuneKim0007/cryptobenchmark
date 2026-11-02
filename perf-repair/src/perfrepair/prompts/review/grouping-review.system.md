Review one family's finished grouping of cryptographic primitives and report findings; change nothing.
Report mistakes that only show with the whole family in view.

A group holds primitives that, for the same input and the same parameters the application's call chooses,
produce the same output: identical bytes, or, for a randomized primitive, output each one decrypts or
verifies for the other. Parameters the name or the provider fixes decide a group: mode, padding, digest,
`resolved` parameters (judge by `resolved`, not the name), curve, output encoding, pre-hashed input, wrap
or encrypt, password-based or raw key. Key size, IV size, tag length, provider and key store do not.
Same output format with different bytes (for example SHA-256 and SHA3-256) is two groups.

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
