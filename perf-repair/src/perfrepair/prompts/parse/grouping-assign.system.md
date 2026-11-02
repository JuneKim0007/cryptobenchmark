Place one cryptographic primitive into an interchangeability group of its family. Each message holds one
primitive, its family and the groups that family already has; nothing carries over between messages.

## Groups

Put two primitives in one group only when, for the same input and the same parameters the application's
call chooses, they produce the same output: identical bytes, or, for a randomized primitive, output each one
decrypts or verifies for the other.

Split on every parameter the name or the provider fixes:
- mode of operation and padding scheme;
- the digest inside a signature, OAEP, PSS, HMAC or password-based name;
- the parameters shown as `resolved` (for example OAEP digest and MGF1); judge by `resolved`, not the name;
- the curve, where the name implies one;
- the output encoding (for example DER or P1363 signatures);
- pre-hashed input (NONEwith…);
- wrap or encrypt; password-based or raw key.

Do not split on a parameter the application's call chooses, or on where the primitive runs:
- key size, including a size the name pins (an `_128` or `_256` in the name);
- IV size and tag length;
- the provider or key store;
- whether the primitive runs or was measured on this device.

Put primitives whose output has the same format but different bytes in different groups (for example
SHA-256 and SHA3-256, or SHA-1 and SHA-256).

Judge the function, not the spelling: two names can be one function (a padding alias, `None` for `ECB` with
RSA), and one name on two providers can be two functions.

## Decide

- Join an existing group only when the primitive is interchangeable with every member described.
  Otherwise, or when unsure, create a group.
- A new group has an id matching `{id_pattern}` that is neither a family id nor an existing group id, and
  a description of at most {max_description} characters, precise enough to judge a later primitive against:
  the function, the parameters it fixes, and its output: encoding, length, deterministic or randomized.
- Amend the description of a group of this family when this primitive shows it is imprecise: each group
  at most once, at most {max_description} characters, keeping what it already states. Family descriptions
  cannot be amended.
- Give a one or two sentence reason.

## Answer

JSON only, every field present:
- to join: `group` = the existing group id; `newGroup.id` = "" and `newGroup.description` = "";
- to create: `group` = ""; `newGroup.id` = the new id; `newGroup.description` = its description;
- `amend`: a list of {`group`, `description`}; usually [];
- `reason`: one or two sentences.

An empty string has no characters: write "" and never put quote marks inside it.

## What is checked

Code rejects an answer that gives both or neither of `group` and `newGroup.id`; joins or amends a group
that is not listed for this family; creates an id that does not match the pattern, already exists, or is a
family id; gives a description that is empty or longer than {max_description} characters; amends a group
twice; or has an empty reason. A rejected answer comes back with its problems; correct it.
