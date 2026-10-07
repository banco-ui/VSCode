"""Discovery service — Phase 14.

Orchestrates the discovery pipeline:

    ProviderAdapter
        ↓
    RawProviderSnapshot
        ↓
    ProviderNormalizer
        ↓
    NormalizationResult
        ↓
    CanonicalInventory + DiscoveryResult

This service does NOT modify adapters, normalizers, or canonical models.
It composes existing Phase 13G contracts into a discovery flow.
"""
from __future__ import annotations

from typing import Optional

from server_manager.discovery.models import (
    CanonicalInventory,
    DiscoveryResult,
)
from server_manager.models.canonical import PlatformType
from server_manager.normalizers.provider_normalizer import (
    NormalizationResult, ProviderNormalizer,
)
from server_manager.orchestrator.models import OrchestrationStatus
from server_manager.providers import (
    AdapterCapability,
    ProviderAdapter,
    RawProviderSnapshot,
)


class PlatformDiscovery:
    """Platform discovery orchestrator.

    Takes a ProviderAdapter and a ProviderNormalizer, runs the full
    discovery pipeline, and returns a DiscoveryResult.

    Usage::

        adapter = KubernetesProviderAdapter(fixture=fixture)
        normalizer = KubernetesProviderNormalizer()
        discovery = PlatformDiscovery()
        result = discovery.discover(adapter, normalizer)

    The discovery service is stateless and does not persist results.
    """

    def discover(
        self,
        adapter: ProviderAdapter,
        normalizer: ProviderNormalizer,
    ) -> DiscoveryResult:
        """Run discovery: adapter → snapshot → normalizer → result.

        Args:
            adapter: Provider adapter (fixture, mock, or live).
            normalizer: Provider normalizer matching the adapter.

        Returns:
            DiscoveryResult with canonical inventory and status.
        """
        # ── Step 1: Collect raw snapshot ────────────────────────────
        snapshot = adapter.collect()

        # ── Step 2: Handle SKIPPED (e.g., no credentials) ───────────
        if snapshot.collection_status == OrchestrationStatus.SKIPPED:
            return self._build_skipped_result(snapshot)

        # ── Step 3: Normalize snapshot → canonical entities ────────
        norm_result = normalizer.normalize(snapshot)

        # ── Step 4: Build canonical inventory ────────────────────────
        inventory = CanonicalInventory.from_normalization(
            norm_result,
            provider_id=snapshot.provider_id,
        )

        # ── Step 5: Derive discovery status ─────────────────────────
        discovery_status = self._derive_discovery_status(snapshot, norm_result)

        # ── Step 6: Collect capability summary ──────────────────────
        caps_attempted = [cr.capability for cr in snapshot.capability_results]
        caps_succeeded = list(snapshot.successful_capabilities)
        caps_failed = list(snapshot.failed_capabilities)

        # ── Step 7: Aggregate errors and warnings ────────────────────
        errors: list[str] = list(snapshot.errors)
        errors.extend(
            f"[{e.entity_type}] {e.message}" for e in norm_result.errors
        )
        warnings: list[str] = list(snapshot.warnings)
        warnings.extend(norm_result.warnings)

        # ── Step 8: Identified platform ─────────────────────────────
        identified_type = PlatformType.UNKNOWN
        if inventory.platforms:
            identified_type = inventory.platforms[0].platform_type

        return DiscoveryResult(
            provider_type=snapshot.provider_type,
            provider_id=snapshot.provider_id,
            discovery_status=discovery_status,
            snapshot_id=snapshot.snapshot_id,
            collected_at=snapshot.collected_at,
            identified_platform_type=identified_type,
            inventory=inventory,
            capabilities_attempted=caps_attempted,
            capabilities_succeeded=caps_succeeded,
            capabilities_failed=caps_failed,
            relationship_evidence=list(snapshot.relationship_evidence),
            errors=errors,
            warnings=warnings,
        )

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _derive_discovery_status(
        snapshot: RawProviderSnapshot,
        norm_result: NormalizationResult,
    ) -> OrchestrationStatus:
        """Derive overall discovery status from snapshot + normalization.

        Rules:
            - If snapshot collection was SKIPPED → SKIPPED
            - If snapshot was FAILED and no entities produced → FAILED
            - If snapshot was PARTIAL or normalization had errors → PARTIAL
            - Otherwise → SUCCESS
        """
        if snapshot.collection_status == OrchestrationStatus.SKIPPED:
            return OrchestrationStatus.SKIPPED

        if (
            snapshot.collection_status == OrchestrationStatus.FAILED
            and norm_result.is_empty
        ):
            return OrchestrationStatus.FAILED

        if snapshot.collection_status == OrchestrationStatus.PARTIAL:
            return OrchestrationStatus.PARTIAL

        if norm_result.errors:
            return OrchestrationStatus.PARTIAL

        return OrchestrationStatus.SUCCESS

    @staticmethod
    def _build_skipped_result(snapshot: RawProviderSnapshot) -> DiscoveryResult:
        """Build a SKIPPED discovery result (e.g., no credentials)."""
        return DiscoveryResult(
            provider_type=snapshot.provider_type,
            provider_id=snapshot.provider_id,
            discovery_status=OrchestrationStatus.SKIPPED,
            snapshot_id=snapshot.snapshot_id,
            collected_at=snapshot.collected_at,
            inventory=None,
            errors=list(snapshot.errors),
            warnings=["Discovery skipped: external preconditions not met"],
        )
