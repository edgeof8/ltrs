# JSON-safe cache encodings. Never pickle: a shared cache file must not load code.
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from .aop_value import AoPValue

CACHE_VERSION = 3
CACHE_FILENAME = "precalculated_cache_v3.json"


def empty_cache() -> Dict[str, Any]:
    return {"version": CACHE_VERSION, "by_poly": {}, "by_expression": {}}


def is_usable_cache(data: Any) -> bool:
    if not isinstance(data, dict) or data.get("version") != CACHE_VERSION:
        return False
    if "raw_pickle" in data:
        return False
    return isinstance(data.get("by_poly"), dict) and isinstance(
        data.get("by_expression"), dict
    )


def encode_aop_value(val: AoPValue) -> Dict[str, Any]:
    poly = {str(k): str(v) for k, v in val._rust_obj.get_poly().items()}
    return {
        "base": int(val._rust_obj.base),
        "coeff": str(val._rust_obj.coeff),
        "poly": poly,
    }


def decode_aop_value(payload: Dict[str, Any]) -> AoPValue:
    poly = {str(k): int(v) for k, v in payload["poly"].items()}
    return AoPValue(poly=poly, base=int(payload["base"]), coeff=int(payload["coeff"]))


def poly_key(encoded: Dict[str, Any]) -> str:
    terms = sorted(encoded["poly"].items(), key=lambda kv: int(kv[0]))
    return json.dumps(
        {"base": encoded["base"], "coeff": encoded["coeff"], "terms": terms},
        separators=(",", ":"),
    )


def expression_key(expression: str, base: int) -> str:
    return f"{base}:{expression}"


def expression_is_cacheable(expression: str) -> bool:
    # Results that mention variables depend on calculator state, not just the poly.
    return "$" not in expression


def find_poly_entry(
    cache: Optional[Dict[str, Any]], expression: str, base: int
) -> Optional[Tuple[str, Dict[str, Any]]]:
    if not cache or not expression_is_cacheable(expression):
        return None
    key = cache["by_expression"].get(expression_key(expression, base))
    if not key:
        return None
    entry = cache["by_poly"].get(key)
    if not isinstance(entry, dict):
        return None
    return key, entry


def store_result(
    cache: Dict[str, Any],
    expression: str,
    mode: str,
    encoded: Dict[str, Any],
    formatted: str,
) -> None:
    key = poly_key(encoded)
    entry = cache["by_poly"].get(key)
    if entry is None:
        entry = {
            "base": encoded["base"],
            "coeff": encoded["coeff"],
            "poly": encoded["poly"],
        }
        cache["by_poly"][key] = entry
    entry[mode] = formatted
    if expression_is_cacheable(expression):
        cache["by_expression"][expression_key(expression, encoded["base"])] = key
