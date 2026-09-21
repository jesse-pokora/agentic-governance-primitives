"""Persona/capability catalog: "who is allowed to do what."

Loads and validates a declarative YAML catalog against a JSON Schema.
Deliberately has no knowledge of, and no import of, anything about what is
actually running right now — see runtime.py for that, kept fully separate.
"""

from __future__ import annotations

import json
import os

import yaml
from jsonschema import validate as jsonschema_validate

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CATALOG_PATH = os.path.join(_HERE, "catalog.yaml")
DEFAULT_SCHEMA_PATH = os.path.join(_HERE, "schema.json")


def load_schema(schema_path: str = DEFAULT_SCHEMA_PATH) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_catalog(catalog_path: str = DEFAULT_CATALOG_PATH) -> dict:
    with open(catalog_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def audit_catalog(catalog_path: str = DEFAULT_CATALOG_PATH, schema_path: str = DEFAULT_SCHEMA_PATH) -> dict:
    """Load and validate the catalog, returning it if valid.

    Raises jsonschema.ValidationError if any persona lists a capability
    outside the fixed vocabulary, or the shape is otherwise malformed.
    Never touches any runtime process state to do this.
    """
    catalog = load_catalog(catalog_path)
    schema = load_schema(schema_path)
    jsonschema_validate(instance=catalog, schema=schema)
    return catalog


def capabilities_of(catalog: dict, persona_name: str) -> list[str]:
    return catalog["personas"][persona_name]["capabilities"]
