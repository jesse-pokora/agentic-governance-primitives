"""Deterministic embedding-request contract check.

An embedding call's provider, model ID, version, and dimensions can be
verified byte-for-byte against a captured request — with no live AWS (or
any other) network call. This module makes no network-related imports at
all; the check is a pure dict comparison.
"""

from __future__ import annotations

CONTRACT_FIELDS = ("provider", "model_id", "version", "dimensions")


class ContractMismatch(Exception):
    def __init__(self, mismatched_fields: dict):
        super().__init__(f"contract_mismatch: {mismatched_fields}")
        self.mismatched_fields = mismatched_fields


def verify_request_contract(actual_request: dict, expected_contract: dict) -> None:
    """Raise ContractMismatch listing every field that doesn't match
    byte-for-byte. Never makes a network call — this only ever compares
    two already-captured dicts.
    """
    mismatched = {}
    for field in CONTRACT_FIELDS:
        actual_value = actual_request.get(field)
        expected_value = expected_contract.get(field)
        if actual_value != expected_value:
            mismatched[field] = {"expected": expected_value, "actual": actual_value}

    if mismatched:
        raise ContractMismatch(mismatched)
