from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AntResult:
    success: bool
    data: Any = None
    content: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Ant(ABC):
    """
    Abstract Base Class for all Ants.
    Ants are atomic workers that perform a specific task.
    """

    @abstractmethod
    def execute(self, payload: Any, context: Dict[str, Any]) -> AntResult:
        """
        Execute the Ant's task.
        :param payload: The specific data to work on (e.g., a DocumentNode).
        :param context: Global context (e.g., project summary, API keys).
        :return: AntResult
        """
        pass
