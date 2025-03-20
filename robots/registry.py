"""Tool registry for managing and executing tools."""

from typing import Any, Dict, List, Optional, Type

from robots.tools.base import Tool


class ToolRegistry:
    """Registry for managing and executing tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool with the registry.
        
        Args:
            tool: The tool instance to register.
        """
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool from the registry.
        
        Args:
            tool_name: The name of the tool to unregister.
        """
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.
        
        Args:
            name: The name of the tool to get.
            
        Returns:
            The tool if found, None otherwise.
        """
        return self._tools.get(name)

    async def execute(self, name: str, input_data: Dict[str, Any]) -> str:
        """Execute a tool.
        
        Args:
            name: The name of the tool to execute.
            input_data: The input data for the tool.
            
        Returns:
            The result of executing the tool.
        """
        tool = self.get_tool(name)
        if tool:
            return await tool.execute(input_data)
        return f"Error: Tool {name} not found"

    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered tools.
        
        Returns:
            A list of dictionaries containing tool information.
        """
        return [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        } for tool in self._tools.values()] 