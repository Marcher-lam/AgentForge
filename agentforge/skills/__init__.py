"""Skill system — SKILL.md format, OpenClaw compatible."""

from agentforge.skills.registry import (
    SkillDependencyNotFoundError,
    SkillNotFoundError,
    SkillRegistry,
)
from agentforge.skills.skill_md import SkillMD

__all__ = [
    "SkillMD",
    "SkillRegistry",
    "SkillNotFoundError",
    "SkillDependencyNotFoundError",
]


class SkillExecutionError(Exception):
    """Raised when a skill handler fails during execution."""
