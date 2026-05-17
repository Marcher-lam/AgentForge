"""LLM unified interface — multi-backend support."""

from agentforge.llm.protocol import (
    LLMBackend,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    TokenUsage,
    ToolCall,
    ToolDefinition,
)


def create_backend(provider: str, **kwargs) -> LLMBackend:
    """Factory: create an LLM backend by provider name."""
    if provider == "openai":
        from agentforge.llm.openai_backend import OpenAIBackend
        return OpenAIBackend(**kwargs)
    elif provider == "anthropic":
        from agentforge.llm.anthropic_backend import AnthropicBackend
        return AnthropicBackend(**kwargs)
    elif provider == "ollama":
        from agentforge.llm.ollama_backend import OllamaBackend
        return OllamaBackend(**kwargs)
    raise ValueError(f"Unknown LLM provider: {provider}")
