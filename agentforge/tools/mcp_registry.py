"""MCP-compliant tool registry with JSON Schema validation."""

from __future__ import annotations

from typing import Any, Callable

import structlog

from agentforge.types.errors import (
    ToolExecutionError,
    ToolNotFoundError,
    ToolValidationError,
)

logger = structlog.get_logger("agentforge.tools.mcp")


# --- JSON Schema types for reference ---
_SCHEMA_TYPES = {"string", "number", "integer", "boolean", "array", "object", "null"}


def _validate_params(params: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate params against a simple JSON Schema. Returns list of error strings."""
    errors: list[str] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field_name in required:
        if field_name not in params:
            errors.append(f"Missing required field: {field_name}")

    # Check types for present fields
    type_map: dict[str, type | tuple[type, ...]] = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    for key, value in params.items():
        if key not in properties:
            continue
        expected_type = properties[key].get("type")
        if expected_type and expected_type in type_map:
            if not isinstance(value, type_map[expected_type]):
                errors.append(
                    f"Field '{key}' expected type {expected_type}, got {type(value).__name__}"
                )

    return errors


class MCPToolRegistry:
    """MCP-compliant tool registry with JSON-RPC 2.0 style schemas."""

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        handler: Callable[..., Any],
        input_schema: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
        description: str = "",
    ) -> None:
        """Register a tool with its handler, input/output schemas, and description."""
        self._tools[name] = {
            "name": name,
            "handler": handler,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "description": description,
        }
        logger.debug("mcp_register_tool", name=name)

    def unregister_tool(self, name: str) -> None:
        """Remove a tool by name."""
        self._tools.pop(name, None)
        logger.debug("mcp_unregister_tool", name=name)

    def invoke_tool(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Invoke a tool by name with params validated against input_schema.

        Returns {"result": ...} on success or {"error": ...} on failure.
        """
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")

        tool = self._tools[name]
        input_schema = tool["input_schema"]

        # Validate params
        errors = _validate_params(params, input_schema)
        if errors:
            raise ToolValidationError(f"Validation failed: {'; '.join(errors)}")

        # Execute handler
        try:
            result = tool["handler"](params)
            return {"result": result}
        except Exception as exc:
            raise ToolExecutionError(f"Tool '{name}' execution failed: {exc}") from exc

    def list_tools(self) -> list[dict[str, Any]]:
        """Return all tool definitions with schemas (MCP tools/list style)."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["input_schema"],
                **({"outputSchema": t["output_schema"]} if t["output_schema"] else {}),
            }
            for t in self._tools.values()
        ]
