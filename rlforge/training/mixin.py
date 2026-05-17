"""TrainerMixin — shared training infrastructure."""

from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch

from rlforge.networks.mlp import get_device


class TrainerMixin:
    def setup_seed(self, seed: int | None) -> None:
        if seed is None:
            return
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        self._seed = seed

    def setup_device(self) -> str:
        self._device = get_device()
        return self._device

    def save_checkpoint(self, model: torch.nn.Module, optimizer: torch.optim.Optimizer, path: str, extra: dict | None = None) -> None:
        ckpt = {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
        }
        if extra:
            ckpt.update(extra)
        torch.save(ckpt, path)

    def load_checkpoint(self, model: torch.nn.Module, optimizer: torch.optim.Optimizer, path: str) -> dict:
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        return {k: v for k, v in ckpt.items() if k not in ("model_state_dict", "optimizer_state_dict")}
