from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import os
from src.analysis.project_summary import ProjectSummary


@dataclass
class DocumentNode:
    """Represents a node in the document structure."""

    type: str  # title, chapter, heading, paragraph, etc.
    text: str
    content: Optional[str] = None  # Generated content
    id: str = ""  # Unique ID for reference
    status: str = "pending"  # pending, in_progress, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)


class Blueprint:
    """
    The Blueprint maintains the state of the project and the document.
    It is the Single Source of Truth.
    """

    def __init__(self, project_summary: ProjectSummary):
        self.project_summary = project_summary
        self.document_structure: List[DocumentNode] = []
        self.context: Dict[str, Any] = {}
        self.db_path = "project_memory.json"

    def load_structure(self, structure_data: List[Dict]):
        """Load initial structure from list of dicts."""
        self.document_structure = []
        for i, item in enumerate(structure_data):
            node = DocumentNode(
                type=item.get("type", "unknown"),
                text=item.get("text", ""),
                id=f"node_{i}",
                status="pending",
            )
            self.document_structure.append(node)

    def get_pending_nodes(self) -> List[DocumentNode]:
        """Return list of nodes that need processing."""
        return [n for n in self.document_structure if n.status == "pending"]

    def update_node(
        self,
        node_id: str,
        content: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Update a node's state."""
        for node in self.document_structure:
            if node.id == node_id:
                if content is not None:
                    node.content = content
                if status is not None:
                    node.status = status
                if metadata:
                    node.metadata.update(metadata)
                return True
        return False

    def get_context(self) -> Dict[str, Any]:
        """Return global context."""
        return self.context

    def set_context(self, key: str, value: Any):
        """Set a global context value."""
        self.context[key] = value

    def to_json(self) -> Dict:
        """Serialize state for persistence."""
        return {
            "project_summary": self.project_summary.to_json(),
            "document_structure": [
                {
                    "type": n.type,
                    "text": n.text,
                    "content": n.content,
                    "id": n.id,
                    "status": n.status,
                    "metadata": n.metadata,
                }
                for n in self.document_structure
            ],
            "context": self.context,
        }

    def save(self):
        """Persist state to disk."""
        with open(self.db_path, "w") as f:
            json.dump(self.to_json(), f, indent=2)

    def load(self):
        """Load state from disk."""
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                data = json.load(f)
                # Restore logic would go here
                pass
