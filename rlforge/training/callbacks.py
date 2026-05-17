"""Callback system for training hooks."""

from __future__ import annotations

from typing import Any, Callable
from dataclasses import dataclass


@dataclass
class StepInfo:
    step: int
    reward: float
    loss: float | None = None
    epsilon: float | None = None
    entropy: float | None = None


@dataclass
class EpisodeInfo:
    episode: int
    total_reward: float
    length: int


@dataclass
class UpdateInfo:
    update: int
    loss_dict: dict[str, float]


class Callback:
    def on_step_end(self, info: StepInfo) -> None:
        pass

    def on_episode_end(self, info: EpisodeInfo) -> None:
        pass

    def on_update_end(self, info: UpdateInfo) -> None:
        pass


class CallbackList:
    def __init__(self, callbacks: list[Callback] | None = None) -> None:
        self._callbacks = callbacks or []

    def add(self, cb: Callback) -> None:
        self._callbacks.append(cb)

    def on_step_end(self, info: StepInfo) -> None:
        for cb in self._callbacks:
            cb.on_step_end(info)

    def on_episode_end(self, info: EpisodeInfo) -> None:
        for cb in self._callbacks:
            cb.on_episode_end(info)

    def on_update_end(self, info: UpdateInfo) -> None:
        for cb in self._callbacks:
            cb.on_update_end(info)
