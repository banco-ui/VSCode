"""Base Normalizer (Phase 3).

Abstract base class for all normalizers.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ..models.inventory import ServerInventory

logger = logging.getLogger(__name__)


class BaseNormalizer(ABC):
    """Abstract base class for normalizers.

    Normalizers transform raw collector data into a ServerInventory.
    """

    @property
    def source_name(self) -> str:
        return "base"

    @abstractmethod
    def normalize(self, raw_data: dict[str, Any]) -> ServerInventory:
        """Normalize raw data into ServerInventory.

        Args:
            raw_data: Raw data from a collector.

        Returns:
            ServerInventory instance.
        """
        ...

    def safe_normalize(self, raw_data: dict[str, Any]) -> ServerInventory:
        """Normalize with error handling.

        Returns a minimal ServerInventory on failure.
        """
        try:
            return self.normalize(raw_data)
        except Exception as e:
            logger.error("%s normalization failed: %s", self.source_name, e)
            return ServerInventory()

    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """Safely convert value to int."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_str(value: Any, default: str = "") -> str:
        """Safely convert value to string."""
        if value is None:
            return default
        return str(value).strip()

    @staticmethod
    def parse_bool(value: Any) -> bool:
        """Parse various boolean representations."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("yes", "true", "1", "on")
        if isinstance(value, (int, float)):
            return bool(value)
        return False
