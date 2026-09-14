"""Orchestrator (Phase 5).

Pipeline: Collect → Normalize → Verify → Select Canonical.
Supports fault isolation, run_id tracking, and multi-source orchestration.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from ..models.inventory import ServerInventory
from ..verifiers.base import VerificationResult
from ..verifiers.hardware_verifier import HardwareVerifier
from ..verifiers.os_verifier import OSVerifier
from ..verifiers.runtime_verifier import RuntimeVerifier
from .models import (
    ErrorCategory,
    OrchestrationResult,
    OrchestrationStatus,
    SourceResult,
)

logger = logging.getLogger(__name__)

# Source priority for canonical selection
SOURCE_PRIORITY = ["redfish", "ssh", "ipmi", "snmp"]


class Orchestrator:
    """Orchestrate multi-source collection, normalization, and verification."""

    def __init__(
        self,
        collectors: Optional[dict[str, Callable[[], dict[str, Any]]]] = None,
        normalizers: Optional[dict[str, Callable[[dict[str, Any]], ServerInventory]]] = None,
    ) -> None:
        """
        Args:
            collectors: Dict of source_name → collector callable.
                        Each collector returns raw dict data.
            normalizers: Dict of source_name → normalizer callable.
                         Each normalizer takes raw dict and returns ServerInventory.
        """
        self._collectors = collectors or {}
        self._normalizers = normalizers or {}
        self._hardware_verifier = HardwareVerifier()
        self._os_verifier = OSVerifier()
        self._runtime_verifier = RuntimeVerifier()

    def run(
        self,
        server_id: str,
        collectors: Optional[dict[str, Callable[[], dict[str, Any]]]] = None,
        normalizers: Optional[dict[str, Callable[[dict[str, Any]], ServerInventory]]] = None,
    ) -> OrchestrationResult:
        """Execute the full pipeline.

        Args:
            server_id: Target server identifier.
            collectors: Override collectors for this run.
            normalizers: Override normalizers for this run.

        Returns:
            OrchestrationResult with all source results and canonical inventory.
        """
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc).isoformat()
        start_ts = datetime.now(timezone.utc)

        colls = collectors or self._collectors
        norms = normalizers or self._normalizers

        source_results: list[SourceResult] = []
        normalized_inventories: dict[str, ServerInventory] = {}
        all_errors: list[str] = []
        all_warnings: list[str] = []

        # ── Stage 1+2: Collection + Normalization (per source) ──────
        for source_name in colls:
            sr = SourceResult(source=source_name)
            src_start = datetime.now(timezone.utc)

            # Collection
            try:
                raw_data = colls[source_name]()
                sr.collection_success = True
            except Exception as e:
                sr.collection_success = False
                error_cat = ErrorCategory.from_exception(e)
                error_msg = f"[{source_name}] Collection failed ({error_cat.value}): {e}"
                sr.errors.append(error_msg)
                all_errors.append(error_msg)
                logger.error(error_msg)
                sr.duration_ms = int((datetime.now(timezone.utc) - src_start).total_seconds() * 1000)
                source_results.append(sr)
                continue

            # Normalization
            if source_name in norms:
                try:
                    inv = norms[source_name](raw_data)
                    sr.normalization_success = True
                    sr.inventory = inv
                    normalized_inventories[source_name] = inv
                except Exception as e:
                    sr.normalization_success = False
                    error_cat = ErrorCategory.from_exception(e)
                    error_msg = f"[{source_name}] Normalization failed ({error_cat.value}): {e}"
                    sr.errors.append(error_msg)
                    all_errors.append(error_msg)
                    logger.error(error_msg)
            else:
                sr.normalization_success = False
                warn_msg = f"[{source_name}] No normalizer registered, skipping normalization"
                sr.warnings.append(warn_msg)
                all_warnings.append(warn_msg)

            sr.duration_ms = int((datetime.now(timezone.utc) - src_start).total_seconds() * 1000)
            source_results.append(sr)

        # ── Stage 3: Canonical selection ─────────────────────────────
        canonical_inventory = None
        canonical_source = None

        for source in SOURCE_PRIORITY:
            if source in normalized_inventories:
                canonical_inventory = normalized_inventories[source]
                canonical_source = source
                break

        # Fallback: first available normalized inventory
        if canonical_inventory is None and normalized_inventories:
            canonical_source = list(normalized_inventories.keys())[0]
            canonical_inventory = normalized_inventories[canonical_source]

        # ── Stage 4: Verification ────────────────────────────────────
        verification: Optional[VerificationResult] = None
        verification_success = False

        if len(normalized_inventories) >= 2:
            try:
                hw_result = self._hardware_verifier.verify(normalized_inventories)
                os_result = self._os_verifier.verify(normalized_inventories)
                rt_result = self._runtime_verifier.verify(normalized_inventories)

                # Combine all field results
                all_fields = (
                    hw_result.field_results
                    + os_result.field_results
                    + rt_result.field_results
                )
                verification = VerificationResult(
                    field_results=all_fields,
                    summary={
                        "hardware": hw_result.summary,
                        "os": os_result.summary,
                        "runtime": rt_result.summary,
                        "total_fields": len(all_fields),
                        "discrepancy_count": sum(
                            1 for fr in all_fields if fr.status.value == "DISCREPANCY"
                        ),
                    },
                )
                verification_success = verification.discrepancy_count == 0
            except Exception as e:
                error_msg = f"Verification failed: {e}"
                all_errors.append(error_msg)
                logger.error(error_msg)
        elif len(normalized_inventories) == 1:
            all_warnings.append("Single source only — verification skipped (no cross-source comparison)")

        # ── Determine overall status ────────────────────────────────
        successful_sources = sum(1 for sr in source_results if sr.normalization_success)
        total_sources = len(source_results)

        if successful_sources == 0:
            status = OrchestrationStatus.FAILED
        elif successful_sources < total_sources:
            status = OrchestrationStatus.PARTIAL
        else:
            status = OrchestrationStatus.SUCCESS

        completed_at = datetime.now(timezone.utc).isoformat()
        total_duration_ms = int((datetime.now(timezone.utc) - start_ts).total_seconds() * 1000)

        return OrchestrationResult(
            run_id=run_id,
            server_id=server_id,
            status=status,
            source_results=source_results,
            canonical_inventory=canonical_inventory,
            canonical_source=canonical_source,
            verification=verification,
            verification_success=verification_success,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            errors=all_errors,
            warnings=all_warnings,
        )

    def run_from_inventories(
        self,
        server_id: str,
        inventories: dict[str, ServerInventory],
    ) -> OrchestrationResult:
        """Run verification directly from pre-collected inventories.

        This is useful for testing or when collection is done externally.

        Args:
            server_id: Target server identifier.
            inventories: Dict of source_name → ServerInventory.

        Returns:
            OrchestrationResult with verification results.
        """
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc).isoformat()
        start_ts = datetime.now(timezone.utc)

        source_results: list[SourceResult] = []
        all_errors: list[str] = []
        all_warnings: list[str] = []

        for source_name, inv in inventories.items():
            sr = SourceResult(
                source=source_name,
                collection_success=True,
                normalization_success=True,
                inventory=inv,
                duration_ms=0,
            )
            source_results.append(sr)

        # Canonical selection
        canonical_inventory = None
        canonical_source = None
        for source in SOURCE_PRIORITY:
            if source in inventories:
                canonical_inventory = inventories[source]
                canonical_source = source
                break
        if canonical_inventory is None and inventories:
            canonical_source = list(inventories.keys())[0]
            canonical_inventory = inventories[canonical_source]

        # Verification
        verification: Optional[VerificationResult] = None
        verification_success = False

        if len(inventories) >= 2:
            try:
                hw_result = self._hardware_verifier.verify(inventories)
                os_result = self._os_verifier.verify(inventories)
                rt_result = self._runtime_verifier.verify(inventories)

                all_fields = (
                    hw_result.field_results
                    + os_result.field_results
                    + rt_result.field_results
                )
                verification = VerificationResult(
                    field_results=all_fields,
                    summary={
                        "hardware": hw_result.summary,
                        "os": os_result.summary,
                        "runtime": rt_result.summary,
                        "total_fields": len(all_fields),
                        "discrepancy_count": sum(
                            1 for fr in all_fields if fr.status.value == "DISCREPANCY"
                        ),
                    },
                )
                verification_success = verification.discrepancy_count == 0
            except Exception as e:
                error_msg = f"Verification failed: {e}"
                all_errors.append(error_msg)
                logger.error(error_msg)
        elif len(inventories) == 1:
            all_warnings.append("Single source only — verification skipped")

        successful = sum(1 for sr in source_results if sr.normalization_success)
        total = len(source_results)

        if successful == 0:
            status = OrchestrationStatus.FAILED
        elif successful < total:
            status = OrchestrationStatus.PARTIAL
        else:
            status = OrchestrationStatus.SUCCESS

        completed_at = datetime.now(timezone.utc).isoformat()
        total_duration_ms = int((datetime.now(timezone.utc) - start_ts).total_seconds() * 1000)

        return OrchestrationResult(
            run_id=run_id,
            server_id=server_id,
            status=status,
            source_results=source_results,
            canonical_inventory=canonical_inventory,
            canonical_source=canonical_source,
            verification=verification,
            verification_success=verification_success,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            errors=all_errors,
            warnings=all_warnings,
        )
