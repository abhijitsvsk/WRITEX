from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .code_parser import CodeAnalysisResult


@dataclass
class ProjectSummary:
    project_type: str = "Unknown"
    tech_stack: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    workflow: str = ""
    dataset: str = ""
    algorithms_used: List[str] = field(default_factory=list)
    total_files: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)  # Track test files
    detailed_analysis: Optional["CodeAnalysisResult"] = (
        None  # Real code analysis from AST parser
    )

    def to_json(self):
        """Returns JSON-safe dict. detailed_analysis is NOT included here
        because CodeAnalysisResult is not JSON serializable.
        Access it via summary.detailed_analysis directly."""
        return {
            "project_type": self.project_type,
            "tech_stack": self.tech_stack,
            "modules": self.modules,
            "workflow": self.workflow,
            "dataset": self.dataset,
            "algorithms_used": self.algorithms_used,
            "total_files": self.total_files,
            "languages": self.languages,
            "entry_points": self.entry_points,
            "test_files": self.test_files,
        }
