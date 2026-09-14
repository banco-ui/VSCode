"""Base Collector (Phase 2).

Abstract base class for all collectors.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CollectionResult:
    """Result of a collection operation."""

    def __init__(
        self,
        success: bool = False,
        data: Optional[dict[str, Any]] = None,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ) -> None:
        self.success = success
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)


class BaseCollector(ABC):
    """Abstract base class for all collectors.

    Collectors are responsible for gathering raw data from a source
    (Redfish, SSH, IPMI, SNMP). They do NOT normalize data — that's
    the Normalizer's job.
    """

    def __init__(self, host: str, port: int = 443, username: str = "", password: str = "") -> None:
        self.host = host
        self.port = port
        self.username = username
        self._password = password  # Never expose in output

    @property
    def source_name(self) -> str:
        """Return the source name for this collector."""
        return "base"

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """Collect raw data from the source.

        Returns:
            Dict of raw data from the source.

        Raises:
            Exception: If collection fails.
        """
        ...

    def safe_collect(self) -> CollectionResult:
        """Collect with error handling.

        Returns:
            CollectionResult with success/failure status and data.
        """
        result = CollectionResult()
        try:
            data = self.collect()
            result.data = data
            result.success = True
        except Exception as e:
            result.add_error(f"{self.source_name} collection failed: {e}")
            logger.error("%s collection failed: %s", self.source_name, e)
        return result
