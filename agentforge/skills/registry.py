"""Skill registry — SKILL.md native format, OpenClaw compatible.

Skills are stored as SKILL.md files on disk in a skills directory.
This is the same format used by OpenClaw/AgentSkills, ensuring
any skill created for AgentForge works in OpenClaw and vice versa.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import structlog

from agentforge.skills.skill_md import (
    SkillMD,
    delete_skill,
    list_skills as list_skills_from_disk,
    load_skill,
    write_skill,
)
from agentforge.types.errors import (
    AgentForgeError,
    CyclicDependencyError,
    SkillNotFoundError,
)

logger = structlog.get_logger("agentforge.skills")


class SkillDependencyNotFoundError(AgentForgeError):
    """Raised when a required skill dependency is not registered."""


class SkillRegistry:
    """Skill registry backed by SKILL.md files.

    Each skill is a directory containing SKILL.md (YAML frontmatter + instructions).
    The on-disk format is identical to OpenClaw's AgentSkills spec — skills are
    portable between AgentForge and OpenClaw without conversion.
    """

    def __init__(self, skills_dir: str | None = None) -> None:
        self._skills_dir = skills_dir
        # In-memory cache: name -> SkillMD
        self._cache: dict[str, SkillMD] = {}
        # Code-based skill handlers (for internal/synthetic skills without SKILL.md)
        self._handlers: dict[str, Callable[..., Any]] = {}
        # Dependency overrides (for code-registered skills)
        self._deps: dict[str, tuple[str, ...]] = {}

    @property
    def skills_dir(self) -> str:
        if self._skills_dir:
            return self._skills_dir
        # Default: workspace/skills
        return os.path.join(os.getcwd(), "skills")

    def install(self, skill: SkillMD) -> str:
        """Install a skill by writing its SKILL.md to disk.

        Returns the path to the created SKILL.md file.
        """
        path = write_skill(self.skills_dir, skill)
        self._cache[skill.name] = skill
        logger.info("skill_installed", name=skill.name, path=str(path))
        return str(path)

    def install_from_text(self, text: str, source_path: str | None = None) -> SkillMD | None:
        """Parse SKILL.md content, validate, and install.

        Returns the parsed SkillMD or None if invalid.
        """
        skill = SkillMD.from_text(text, source_path)
        if not skill.name or skill.name == "unknown":
            return None
        eligible, missing = skill.check_requirements()
        if not eligible:
            logger.warning("skill_requirements_not_met", name=skill.name, missing=missing)
            return None
        self.install(skill)
        return skill

    def uninstall(self, name: str) -> bool:
        """Remove a skill directory from disk."""
        self._cache.pop(name, None)
        self._handlers.pop(name, None)
        return delete_skill(self.skills_dir, name)

    def register_handler(self, name: str, handler: Callable[..., Any], dependencies: list[str] | None = None) -> None:
        """Register a code-based handler for an internal skill.

        For skills that don't have SKILL.md files but need a callable handler.
        """
        self._handlers[name] = handler
        if dependencies:
            self._deps[name] = tuple(dependencies)
        logger.debug("skill_handler_registered", name=name)

    def get(self, name: str) -> SkillMD:
        """Get a skill by name. Loads from disk if not cached."""
        if name in self._cache:
            return self._cache[name]
        skill = load_skill(Path(self.skills_dir) / name)
        if skill is None:
            raise SkillNotFoundError(f"Skill not found: {name}")
        self._cache[name] = skill
        return skill

    def list_skills(self) -> list[SkillMD]:
        """List all installed skills from disk."""
        skills = list_skills_from_disk(self.skills_dir)
        # Update cache
        self._cache = {s.name: s for s in skills}
        return skills

    def get_instructions(self, name: str) -> str:
        """Get the instruction text for a skill (for prompt injection)."""
        skill = self.get(name)
        return skill.instructions

    def get_all_instructions(self) -> list[dict[str, str]]:
        """Get all skill instructions for agent prompt injection."""
        return [{"name": s.name, "instructions": s.instructions} for s in self.list_skills()]

    def execute(self, name: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a skill.

        For code-handler skills: calls the handler with context.
        For SKILL.md skills: returns the instructions for the agent to follow.
        """
        handler = self._handlers.get(name)
        if handler:
            result = handler(context)
            return result if isinstance(result, dict) else {"result": result}

        # SKILL.md skills return their instructions
        skill = self.get(name)
        return {
            "type": "skill_instructions",
            "name": skill.name,
            "instructions": skill.instructions,
            "context": context,
        }

    def find_by_tag(self, tag: str) -> list[SkillMD]:
        """Find skills whose metadata contains the given tag."""
        return [
            s for s in self.list_skills()
            if tag in s.metadata.get("tags", [])
        ]

    def export_skill_md(self, name: str) -> str | None:
        """Export a skill as raw SKILL.md text (for download/transfer)."""
        skill = self.get(name)
        return skill.to_text()

    def has_skill(self, name: str) -> bool:
        """Check if a skill is installed."""
        try:
            self.get(name)
            return True
        except SkillNotFoundError:
            return name in self._handlers
