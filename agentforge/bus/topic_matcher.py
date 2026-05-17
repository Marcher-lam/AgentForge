"""Topic matching with wildcard support (* single-level, ** recursive)."""

from __future__ import annotations


def topic_matches(pattern: str, topic: str) -> bool:
    """Check if a topic string matches a pattern with * and ** wildcards."""
    if pattern == topic:
        return True
    if "**" in pattern:
        prefix = pattern.split("**")[0].rstrip(".")
        return topic.startswith(prefix) if prefix else True
    pattern_parts = pattern.split(".")
    topic_parts = topic.split(".")
    if len(pattern_parts) != len(topic_parts):
        return False
    return all(p == "*" or p == t for p, t in zip(pattern_parts, topic_parts))
