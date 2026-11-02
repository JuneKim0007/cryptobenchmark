Decide whether replacing one cryptographic primitive with another is worth testing inside an
application. Each message holds one group of interchangeable primitives and its measurements; nothing
carries over between messages.

## What you are given

- The mode: the improvement criterion. Judge only by it.
- Run warnings: conditions under which these numbers were taken that limit how far they transfer.
- Per configuration (operation, key size, input size, phase): each member's median time per
  operation, its 95% bootstrap interval, interquartile range, coefficient of variation, sample count
  and allocations per operation; and every ordered pair "from -> to" with time ratio (to ÷ from;
  below 1 is faster), pImprove (the probability that `to`'s median is lower) with its confidence
  level (`ok` at 95% or more, `warn` from 80%, `weak` below, `too_few_runs` when there is no
  number), the run count, the allocation ratio, the pair's interop check, and whether the mode counts
  it as improving.
- Interop: `pass` (each decrypts or verifies what the other produced, both directions, shared key,
  each at its own defaults), `not_checkable` (the check could not run; not a failure), `not_planned`
  or `not_run` (never checked). Failed pairs are not listed.
- A level grades the evidence; it never forbids a pair. Weigh a `warn` or `weak` pair against the
  size of its gain.

Use the numbers as given; do not recompute or reinterpret them.

## How to decide

- `test` when at least one pair improves under the mode by a margin the measurements support:
  its pImprove and level, in configurations an application plausibly uses.
- `skip` when every improvement is too uncertain for its size, negligible, confined to configurations no
  application would use, or undermined by the run warnings.
- For `test`, list each worthwhile pair with `from`, `to` (member aliases `M1`, `M2`, … as listed) and a
  one-sentence reason naming the configuration(s) that justify it.
- For `skip`, `pairs` is [].

## Answer

JSON only, matching the schema: `decision` (`test` or `skip`), `pairs`, `reason` (not empty).

## What is checked after you answer

Code rejects an answer when a pair names something that is not a member, names the same member
twice, or does not improve under the mode in any configuration; when `test` names no pair; when
`skip` names pairs; or when a reason is empty. A rejected answer comes back with its problems; correct
it. Declining ends the conversation. When every attempt fails, the group is recorded as `skip`.
