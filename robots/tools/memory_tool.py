"""Memory tool for saving messages to a memory file."""

from typing import Any, Dict

from robots.tools.base import Tool


class MemoryTool(Tool):
    """Tool for saving messages to a memory file."""

    @property
    def name(self) -> str:
        """Return the name of the tool."""
        return "memory"

    @property
    def description(self) -> str:
        """Return the description of the tool."""
        return "Save a message to the memory. Useful to remember context between conversations."

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Return the input schema of the tool."""
        return {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"]
        }

    async def execute(self, input_data: Dict[str, Any]) -> str:
        """Execute the memory tool.
        
        Args:
            input_data: Contains the message to save.
            
        Returns:
            Confirmation message.
        """
        try:
            with open("memory.txt", "a") as f:
                f.write(f"---\n{input_data['message']}\n")
            return "Message added to memory"
        except Exception as e:
            return f"Error: {str(e)}" 