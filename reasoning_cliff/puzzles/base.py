"""Abstract puzzle interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from reasoning_cliff.models import PuzzleInstance, VerifierResult


class Puzzle(ABC):
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_instance(self, complexity: int, **kwargs: Any) -> PuzzleInstance:
        raise NotImplementedError

    @abstractmethod
    def verify(self, complexity: int, response_text: str, **kwargs: Any) -> VerifierResult:
        raise NotImplementedError
