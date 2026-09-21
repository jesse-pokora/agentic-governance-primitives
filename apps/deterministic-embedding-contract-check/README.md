# deterministic-embedding-contract-check

**Atomic claim:** An embedding call's provider, model ID, version, and
dimensions can be verified byte-for-byte against a captured request —
with no live AWS call.

**Inspired by:** deterministic embedding-request contract verification
(named for context; this app does not import or depend on that source).

**Enforcement class:** deterministic — every contract field is an exact
equality comparison between two already-captured dicts.

## How it works

`verify_request_contract(actual_request, expected_contract)` compares
exactly four fields — `provider`, `model_id`, `version`, `dimensions` —
between a captured request and the expected contract, byte-for-byte
(plain `!=`, no fuzzy or partial matching). Any other field, like the
actual embedding input text, is irrelevant to the contract and never
compared. A mismatch on any of the four raises `ContractMismatch` listing
every field that failed, both the expected and actual value.

There is no network call anywhere in this module — a test parses its
source with `ast` to confirm it imports nothing network-related (`boto3`,
`requests`, `socket`, etc.), so the "no live AWS call" half of the claim
is structurally enforced, not just asserted in prose.

## Run it

```bash
cd apps/deterministic-embedding-contract-check
python -m unittest test_contract_check.py -v
```

The captured request is a toy fixture resembling an Amazon Bedrock Titan
embedding call — no real credentials or live API access involved.
