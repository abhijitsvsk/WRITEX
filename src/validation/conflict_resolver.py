"""
Conflict detection engine for Special Requests vs Reference Document parameters.
Pure comparison logic — no LLM calls, no UI, no side effects.
"""

from typing import Any, Dict, List, Optional
from src.models.constraints import ConflictRecord

# Maps StyleAnalyzer's analyze_visual_style() output keys to SpecialRequest parameter keys.
# Update this mapping if StyleAnalyzer's return dictionary changes.
STYLE_ANALYZER_KEY_MAP: Dict[str, str] = {
    "font_name": "font_name",
    "font_size": "font_size",
    "line_spacing": "line_spacing",
}

# Human-readable labels for conflict display
PARAMETER_LABELS: Dict[str, str] = {
    "max_pages": "Maximum Page Count",
    "min_pages": "Minimum Page Count",
    "font_size": "Font Size",
    "font_name": "Font Name",
    "line_spacing": "Line Spacing",
    "margin_inches": "Margin Width (inches)",
    "min_words": "Minimum Word Count",
    "max_words": "Maximum Word Count",
}

# Default numeric tolerances — values within tolerance are NOT considered conflicts.
DEFAULT_TOLERANCES: Dict[str, float] = {
    "font_size": 0.5,
    "line_spacing": 0.1,
    "margin_inches": 0.05,
    # Page counts and word counts: zero tolerance (not listed = 0.0)
}


def normalise_reference_params(raw_style_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts StyleAnalyzer output keys into SpecialRequest-compatible keys
    using STYLE_ANALYZER_KEY_MAP. Any unmapped keys are dropped.
    """
    normalised = {}
    for style_key, request_key in STYLE_ANALYZER_KEY_MAP.items():
        if style_key in raw_style_params:
            normalised[request_key] = raw_style_params[style_key]
    return normalised


def detect_conflicts(
    request_params: Dict[str, Any],
    reference_params: Dict[str, Any],
    tolerance: Optional[Dict[str, float]] = None,
) -> List[ConflictRecord]:
    """
    Compares a SpecialRequest's parameters against the extracted reference parameters.
    Returns a list of ConflictRecords for every parameter that differs beyond tolerance.

    Args:
        request_params: The confirmed SpecialRequest.parameters dict.
        reference_params: The normalised reference document parameters dict
                          (already mapped via normalise_reference_params or raw from StyleAnalyzer).
        tolerance: Optional override for numeric tolerances. Merged on top of DEFAULT_TOLERANCES.

    Returns:
        List of ConflictRecord objects with resolved_value=None and resolution_source="".
    """
    effective_tolerance = {**DEFAULT_TOLERANCES}
    if tolerance:
        effective_tolerance.update(tolerance)

    conflicts: List[ConflictRecord] = []

    for key in request_params:
        if key not in reference_params:
            continue  # No conflict if the reference doesn't specify this param

        req_val = request_params[key]
        ref_val = reference_params[key]

        # String comparison (case-insensitive for font names, etc.)
        if isinstance(req_val, str) and isinstance(ref_val, str):
            if req_val.strip().lower() != ref_val.strip().lower():
                conflicts.append(ConflictRecord(
                    parameter_key=key,
                    parameter_label=PARAMETER_LABELS.get(key, key),
                    reference_value=ref_val,
                    request_value=req_val,
                    resolved_value=None,
                    resolution_source="",
                ))
        # Numeric comparison with tolerance
        elif isinstance(req_val, (int, float)) and isinstance(ref_val, (int, float)):
            tol = effective_tolerance.get(key, 0.0)
            if abs(float(req_val) - float(ref_val)) > tol:
                conflicts.append(ConflictRecord(
                    parameter_key=key,
                    parameter_label=PARAMETER_LABELS.get(key, key),
                    reference_value=ref_val,
                    request_value=req_val,
                    resolved_value=None,
                    resolution_source="",
                ))
        # Fallback: strict equality for anything else
        elif req_val != ref_val:
            conflicts.append(ConflictRecord(
                parameter_key=key,
                parameter_label=PARAMETER_LABELS.get(key, key),
                reference_value=ref_val,
                request_value=req_val,
                resolved_value=None,
                resolution_source="",
            ))

    return conflicts


def check_single_conflict(
    parameter_key: str,
    new_value: Any,
    reference_params: Dict[str, Any],
    tolerance: Optional[Dict[str, float]] = None,
) -> bool:
    """
    Checks whether a single new value conflicts with the cached reference params.
    Used during Option 3 re-interpretation to avoid calling detect_conflicts() on the full set.

    Returns True if a conflict exists, False if the value is compatible.
    """
    if parameter_key not in reference_params:
        return False  # No conflict if reference doesn't have this key

    ref_val = reference_params[parameter_key]
    effective_tolerance = {**DEFAULT_TOLERANCES}
    if tolerance:
        effective_tolerance.update(tolerance)

    if isinstance(new_value, str) and isinstance(ref_val, str):
        return new_value.strip().lower() != ref_val.strip().lower()
    elif isinstance(new_value, (int, float)) and isinstance(ref_val, (int, float)):
        tol = effective_tolerance.get(parameter_key, 0.0)
        return abs(float(new_value) - float(ref_val)) > tol
    else:
        return new_value != ref_val
