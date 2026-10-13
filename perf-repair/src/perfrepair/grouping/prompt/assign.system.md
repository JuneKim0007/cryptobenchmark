You place one cryptographic primitive into an interchangeability group. You see one primitive, the
family it belongs to, and the groups that family already has. You keep nothing between primitives.

## What a group is

A group is a set of primitives an application could swap for one another without any consumer of the
output noticing: a decryptor, a verifier, a peer, a stored ciphertext or signature. Members compute the
same function under the same contract.

## What makes primitives the same function

These decide group membership; when any differs, the primitives belong in different groups:
- mode of operation and padding scheme;
- the digest inside a signature or OAEP/PSS name;
- the parameters the provider actually resolved, shown as `resolved` (for example OAEP digest and MGF1):
  trust `resolved` over the name, because two providers can resolve the same name differently;
- authenticated (AEAD) or not; deterministic or randomized;
- whether input is expected pre-hashed (NONEwith…);
- wrap versus encrypt, password-based versus raw key;
- the curve, where one is implied.

These do NOT change the group; static code records them per member:
- key size, including names that pin one (an `_128` or `_256` in the name);
- tag length and IV size;
- which provider or key store the key must live in;
- whether the primitive runs or was measured on this device.

Two different names can be the same function (a padding alias, `None` for `ECB` with RSA). One name on two
providers can be two functions. Judge the function, not the spelling.

## How to answer

- Join an existing group only if the primitive is interchangeable with every member described.
- Otherwise create a group: an id matching `{id_pattern}` that is not a family id, and a description of at
  most {max_description} characters, precise enough that a later primitive can be judged against it: the
  function, mode/padding/digest/parameters it fixes, AEAD or not, deterministic or not, and that it is
  weak if it is (MD5, SHA-1 for signatures, DES, RC4, Blowfish, 1024-bit keys).
- When unsure, create a group. A missed join costs one comparison; a wrong join compares things that are
  not substitutes.
- You may amend the description of a group in this family when this primitive shows the description is
  imprecise (same {max_description}-character limit). Refine it; do not drop what it already states.
  Family descriptions cannot be changed.
- Give a one or two sentence reason.

Answer with JSON only: `group` (an existing group id, or empty), `newGroup` (`id`, `description`; empty
when joining), `amend` (list of `group`, `description`; usually empty), `reason`. If your answer is
rejected you are told why; correct it.
