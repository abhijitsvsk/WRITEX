"""
Data models for the Special Requests with Conflict Resolution feature.
Pure dataclasses — no logic, no imports beyond stdlib.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict


@dataclass
class SpecialRequest:
    """Structured representation of a user's freeform formatting request."""
    raw_text: str
    interpreted_summary: str  # Human-readable, shown to user for confirmation
    parameters: Dict[str, Any] = field(default_factory=dict)
    # Example parameters:
    # { "max_pages": 30, "font_size": 15, "font_name": "Times New Roman",
    #   "line_spacing": 1.5, "margin_inches": 1.0, "min_words": 8000 }
    custom_directives: List[str] = field(default_factory=list)


@dataclass
class ConflictRecord:
    """Records a single conflict between a special request and the reference document."""
    parameter_key: str
    parameter_label: str       # Human-readable label, e.g. "Font Size"
    reference_value: Any       # Value from the sample report
    request_value: Any         # Value from special request
    resolved_value: Any = None       # Filled after user resolves
    resolution_source: str = ""      # "reference", "request", or "new_request"


@dataclass
class ResolvedConstraints:
    """Final merged constraint set passed to DocumentCompiler after all conflicts are resolved."""
    page_limit: Optional[int] = None
    font_size: Optional[int] = None
    font_name: Optional[str] = None
    line_spacing: Optional[float] = None
    margin_inches: Optional[float] = None
    min_words: Optional[int] = None
    max_words: Optional[int] = None
    custom_directives: List[str] = field(default_factory=list)
    source_log: List[ConflictRecord] = field(default_factory=list)  # Full audit trail
