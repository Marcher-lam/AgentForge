"""Exception hierarchy for AgentForge."""


class AgentForgeError(Exception):
    """Base exception for all AgentForge errors."""


class AgentError(AgentForgeError):
    """Agent lifecycle errors."""


class InvalidStateTransition(AgentError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_state: str, to_state: str) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid transition: {from_state} → {to_state}")


class AgentInitFailed(AgentError):
    """Raised when agent initialization fails (non-retryable)."""


class BusError(AgentForgeError):
    """Message bus errors."""


class SubscriptionNotFound(BusError):
    """Raised when unsubscribe is called with unknown subscription_id."""


class RpcTimeout(BusError):
    """Raised when RPC request times out."""


class BusConnectionError(BusError):
    """Raised when a WebSocket bus connection fails."""


class MessageTimeoutError(BusError):
    """Raised when a message or RPC operation times out."""


class MessageDecodeError(BusError):
    """Raised when a message cannot be decoded (invalid JSON or missing fields)."""


class DeliveryError(BusError):
    """Raised when message delivery fails."""


class ConfigError(AgentForgeError):
    """Configuration errors."""


class ToolNotFoundError(AgentForgeError):
    """Raised when a requested tool is not found in the registry."""


class ToolValidationError(AgentForgeError):
    """Raised when tool parameter validation fails."""


class ToolExecutionError(AgentForgeError):
    """Raised when tool execution encounters an error."""


class SkillNotFoundError(AgentForgeError):
    """Raised when a requested skill is not found in the registry."""


class SkillTimeoutError(AgentForgeError):
    """Raised when skill execution exceeds the allowed time."""


class CyclicDependencyError(AgentForgeError):
    """Raised when a cyclic dependency is detected."""


class MCPConnectionError(AgentForgeError):
    """Raised when a connection to an MCP server fails."""
