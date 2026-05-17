"""SKILL.md format parser and writer — AgentSkills / OpenClaw compatible.

The SKILL.md format is the standard skill definition format used by both
AgentForge and OpenClaw. A skill is a directory containing a SKILL.md file
with YAML frontmatter and instruction body. This ensures skills are
interoperable between the two systems.

SKILL.md structure:
    ---
    name: my-skill
    description: What this skill does
    ---

    # Instructions for the agent
    ...
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger("agentforge.skills.skill_md")


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from SKILL.md text.

    Returns (metadata_dict, instruction_body).
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not match:
        return {}, text

    raw = match.group(1)
    body = match.group(2)

    meta: dict[str, Any] = {}
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        colon = line.find(":")
        if colon == -1:
            continue
        key = line[:colon].strip()
        val = line[colon + 1:].strip()

        # Strip quotes
        for q in ('"', "'"):
            if val.startswith(q) and val.endswith(q) and len(val) >= 2:
                val = val[1:-1]
                break

        # Type coercion
        if val.lower() in ("true",):
            val = True
        elif val.lower() in ("false",):
            val = False
        elif re.match(r"^-?\d+$", val):
            val = int(val)
        elif re.match(r"^-?\d+\.\d+$", val):
            val = float(val)
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            val = [v.strip().strip("'\"") for v in inner.split(",")] if inner else []
        elif val.startswith("{"):
            import json
            try:
                val = json.loads(val)
            except (json.JSONDecodeError, ValueError):
                pass

        meta[key] = val

    return meta, body


def _serialize_frontmatter(meta: dict[str, Any]) -> str:
    """Serialize metadata dict back to YAML frontmatter lines."""
    lines: list[str] = []
    for key, val in meta.items():
        if val is None:
            continue
        if isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif isinstance(val, str):
            if any(c in val for c in (":", "#", "{", "}", '"')):
                lines.append(f'{key}: "{val}"')
            else:
                lines.append(f"{key}: {val}")
        elif isinstance(val, (int, float)):
            lines.append(f"{key}: {val}")
        elif isinstance(val, list):
            items = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in val)
            lines.append(f"{key}: [{items}]")
        elif isinstance(val, dict):
            import json
            lines.append(f"{key}: {json.dumps(val, ensure_ascii=False)}")
    return "\n".join(lines)


@dataclass
class SkillMD:
    """Represents a parsed SKILL.md — the standard skill format.

    Compatible with OpenClaw's AgentSkills spec. Any SkillMD written to disk
    as SKILL.md can be loaded by OpenClaw, and vice versa.
    """

    name: str
    description: str
    instructions: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: str | None = None

    @classmethod
    def from_text(cls, text: str, source_path: str | None = None) -> SkillMD:
        """Parse SKILL.md content string."""
        meta, body = _parse_frontmatter(text)
        return cls(
            name=meta.get("name", "unknown"),
            description=meta.get("description", ""),
            instructions=body.strip(),
            metadata=meta.get("metadata", {}),
            source_path=source_path,
        )

    def to_text(self) -> str:
        """Serialize back to SKILL.md format."""
        fm: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
        }
        if self.metadata:
            fm["metadata"] = self.metadata
        return f"---\n{_serialize_frontmatter(fm)}\n---\n\n{self.instructions}\n"

    def check_requirements(self) -> tuple[bool, list[str]]:
        """Check gating requirements from metadata.openclaw.requires.

        Returns (eligible, list_of_missing).
        """
        missing: list[str] = []
        oc = self.metadata.get("openclaw", {})
        if not isinstance(oc, dict):
            return True, []
        if oc.get("always"):
            return True, []

        # OS
        allowed_os = oc.get("os")
        if allowed_os:
            import platform
            current = {"darwin": "darwin", "linux": "linux", "win32": "win32"}.get(
                platform.system().lower(), ""
            )
            if current not in allowed_os:
                missing.append(f"OS mismatch: requires {allowed_os}")

        reqs = oc.get("requires", {})
        if not isinstance(reqs, dict):
            return True, []

        for b in reqs.get("bins", []):
            if not _which(b):
                missing.append(f"missing binary: {b}")

        any_bins = reqs.get("anyBins", [])
        if any_bins and not any(_which(b) for b in any_bins):
            missing.append(f"missing any of: {any_bins}")

        for e in reqs.get("env", []):
            if not os.environ.get(e):
                missing.append(f"missing env: {e}")

        return len(missing) == 0, missing


def _which(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None


def load_skill(path: str | Path) -> SkillMD | None:
    """Load a skill from a SKILL.md file path or skill directory."""
    p = Path(path)
    if p.is_file() and p.name == "SKILL.md":
        return _read_skill_md(p)
    if p.is_dir():
        md = p / "SKILL.md"
        if md.is_file():
            return _read_skill_md(md)
    return None


def _read_skill_md(p: Path) -> SkillMD | None:
    try:
        text = p.read_text(encoding="utf-8")
        skill = SkillMD.from_text(text, str(p))
        return skill if skill.name != "unknown" else None
    except Exception as exc:
        logger.warning("skill_md_load_failed", path=str(p), error=str(exc))
        return None


def write_skill(skills_dir: str | Path, skill: SkillMD) -> Path:
    """Write a skill as SKILL.md to the skills directory.

    Creates `skills_dir/{name}/SKILL.md`. This file is directly usable
    by OpenClaw — same format, same structure.
    """
    base = Path(skills_dir)
    skill_dir = base / skill.name
    skill_dir.mkdir(parents=True, exist_ok=True)
    md_path = skill_dir / "SKILL.md"
    md_path.write_text(skill.to_text(), encoding="utf-8")
    logger.info("skill_md_written", name=skill.name, path=str(md_path))
    return md_path


def delete_skill(skills_dir: str | Path, name: str) -> bool:
    """Remove a skill directory from the skills store."""
    import shutil
    skill_dir = Path(skills_dir) / name
    if skill_dir.is_dir():
        shutil.rmtree(skill_dir)
        logger.info("skill_md_deleted", name=name)
        return True
    return False


def list_skills(skills_dir: str | Path) -> list[SkillMD]:
    """Scan a skills directory and return all parsed skills.

    Supports flat layout: skills/{name}/SKILL.md
    And one-level grouping: skills/{group}/{name}/SKILL.md
    """
    base = Path(skills_dir)
    if not base.is_dir():
        return []

    skills: list[SkillMD] = []
    _scan_dir(base, skills, depth=0)
    return skills


def _scan_dir(base: Path, results: list[SkillMD], depth: int) -> None:
    """Recursively scan for SKILL.md files (max depth 2 for grouping)."""
    for child in sorted(base.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            md = child / "SKILL.md"
            if md.is_file():
                skill = _read_skill_md(md)
                if skill:
                    results.append(skill)
            elif depth < 1:
                _scan_dir(child, results, depth + 1)
