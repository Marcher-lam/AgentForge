"""AgentState enum and valid transition table."""

from __future__ import annotations

from enum import Enum


class AgentState(Enum):
    """Agent lifecycle states."""
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    DESTROYED = "destroyed"


VALID_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.CREATED: {AgentState.INITIALIZED, AgentState.DESTROYED},
    AgentState.INITIALIZED: {AgentState.RUNNING, AgentState.DESTROYED},
    AgentState.RUNNING: {AgentState.STOPPED, AgentState.DESTROYED},
    AgentState.STOPPED: {AgentState.RUNNING, AgentState.DESTROYED},
    AgentState.DESTROYED: set(),
}


def is_valid_transition(from_state: AgentState, to_state: AgentState) -> bool:
    """Check whether a state transition is allowed by the transition table."""
    return to_state in VALID_TRANSITIONS.get(from_state, set())
