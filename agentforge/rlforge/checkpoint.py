"""Checkpoint save/load for RL trainers (JSON-based, NumPy only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _to_serializable(obj: Any) -> Any:
    """Convert numpy arrays and python objects to JSON-serializable form."""
    import numpy as np

    if isinstance(obj, np.ndarray):
        return {"__ndarray__": True, "data": obj.tolist(), "dtype": str(obj.dtype)}
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(v) for v in obj]
    return obj


def _from_serializable(obj: Any) -> Any:
    """Reconstruct numpy arrays from serialized form."""
    import numpy as np

    if isinstance(obj, dict):
        if obj.get("__ndarray__"):
            return np.array(obj["data"], dtype=obj.get("dtype", "float64"))
        return {k: _from_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_from_serializable(v) for v in obj]
    return obj


def save_checkpoint(trainer: Any, path: str) -> None:
    """Save trainer network weights + optimizer state + step count as JSON."""
    state: dict[str, Any] = {"total_steps": getattr(trainer, "total_steps_done", 0)}

    # Save network weights
    if hasattr(trainer, "model"):
        # PPOTrainer uses ActorCritic
        state["network"] = trainer.model.get_weights()
    elif hasattr(trainer, "q_network"):
        # DQNTrainer uses DQNNetwork
        state["network"] = trainer.q_network.get_weights()
        state["target_network"] = trainer.target_network.get_weights()

    # Save optimizer state if accessible
    network = getattr(trainer, "model", None) or getattr(trainer, "q_network", None)
    if network and hasattr(network, "_m") and network._m:
        state["optimizer_m"] = network._m
        state["optimizer_v"] = network._v
        state["optimizer_t"] = network._t

    serialized = _to_serializable(state)

    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w") as f:
        json.dump(serialized, f)


def load_checkpoint(path: str) -> dict:
    """Load checkpoint from JSON file."""
    with open(path, "r") as f:
        serialized = json.load(f)
    return _from_serializable(serialized)
