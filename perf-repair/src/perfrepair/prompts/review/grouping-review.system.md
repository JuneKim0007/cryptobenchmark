Review one family's finished grouping of cryptographic primitives and report findings; change nothing.
Report mistakes that only show with the whole family in view.

Judge a group by three contracts; its members must match on all three:
- input contract: the data and parameters the call passes, and which side supplies each one (a different side
  supplying a parameter, pre-hashed input, wrap or encrypt, password-based or raw key each decide a group);
- key contract: the `key:` shown on a member: `application-held` is key material the application holds;
  `inside the provider` is a handle to a key that lives inside the provider; different values decide a group; a
  member without `key:` is judged by the other two contracts;
- output contract: for the same input, key and call-chosen parameters, identical bytes, or, for a randomized
  primitive, output each one decrypts or verifies for the other (mode, padding, digest, `resolved` parameters,
  curve and output encoding each decide a group; judge by `resolved`, not the name).

Do not report a difference in key size (except the derived key length of a password-based name), IV size, tag
length, provider identity, or whether a member runs here.
Report the same output format with different bytes (for example SHA-256 and SHA3-256) as two groups.

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
