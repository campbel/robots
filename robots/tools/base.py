"""Base tool interface that all tools must implement."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return the description of the tool."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Return the input schema of the tool."""
        pass

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> str:
        """Execute the tool with the given input data.
        
        Args:
            input_data: The input data for the tool.
            
        Returns:
            The result of executing the tool.
        """
        pass 