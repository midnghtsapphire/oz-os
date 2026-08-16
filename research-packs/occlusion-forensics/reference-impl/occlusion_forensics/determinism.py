"""Determinism envelope.

Every analysis run emits a manifest recording the exact inputs, parameters and
library versions that produced it. Two runs with the same manifest hash MUST
produce byte-identical output; this is what makes a result re-checkable by an
opposing analyst rather than merely persuasive.

No module in this package may call a random number generator. There is nothing
to seed because nothing is stochastic.
"""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import scipy

__all__ = [
    "canonical_json",
    "sha256_bytes",
    "sha256_file",
    "sha256_array",
    "RunManifest",
]


def canonical_json(obj: Any) -> str:
    """Serialise with sorted keys and no incidental whitespace.

    Canonicalisation is what makes the parameter hash stable across runs; a
    dict that merely *compares* equal must also *hash* equal.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_array(arr: np.ndarray) -> str:
    """Hash an array by its exact bytes, dtype and shape.

    ``np.ascontiguousarray`` normalises stride layout so that a view and its
    copy hash identically.
    """
    a = np.ascontiguousarray(arr)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(str(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()


@dataclass
class RunManifest:
    """Reproducibility record for a single analysis run."""

    tool_version: str
    inputs: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)

    def add_input(self, label: str, path: str | Path) -> None:
        self.inputs[label] = sha256_file(path)

    def add_array_input(self, label: str, arr: np.ndarray) -> None:
        self.inputs[label] = sha256_array(arr)

    def add_output(self, label: str, arr: np.ndarray) -> None:
        self.outputs[label] = sha256_array(arr)

    def environment(self) -> dict[str, str]:
        return {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_version": self.tool_version,
            "environment": self.environment(),
            "inputs": dict(sorted(self.inputs.items())),
            "parameters": dict(sorted(self.parameters.items())),
            "outputs": dict(sorted(self.outputs.items())),
        }

    def manifest_hash(self) -> str:
        """Hash of everything except the outputs.

        Excluding outputs is deliberate: the manifest hash answers "was this
        the same experiment?", which must be answerable *before* comparing
        results. Same manifest hash with different output hashes is a
        reproducibility failure and should be treated as one.
        """
        payload = self.to_dict()
        payload.pop("outputs")
        return sha256_bytes(canonical_json(payload).encode())

    def to_json(self) -> str:
        payload = self.to_dict()
        payload["manifest_hash"] = self.manifest_hash()
        return json.dumps(payload, sort_keys=True, indent=2)
