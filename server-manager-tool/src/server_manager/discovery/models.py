"""Discovery models — Phase 14.

Platform discovery result and canonical inventory abstractions.

These wrap the existing Phase 13G contract (ProviderAdapter →
RawProviderSnapshot → ProviderNormalizer → NormalizationResult)
into a discovery-level result without duplicating any existing
abstraction.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from server_manager.models.canonical import (
    Accelerator, Cluster, ExecutionEnvironment, Network, Node, OS,
    Physical, Platform, PlatformType, ProviderType, Storage, Workload,
)
from server_manager.normalizers.provider_normalizer import NormalizationResult
from server_manager.orchestrator.models import OrchestrationStatus
from server_manager.providers import (
    AdapterCapability, RawRelationshipEvidence,
)


class CanonicalInventory(BaseModel):
    """Aggregated canonical entities from a single discovery run.

    Read-only view of what was discovered — not a persistence model.
    NO_EVIDENCE → NO_ENTITY: lists are empty when provider supplied
    no evidence for that entity type.
    """

    provider_type: ProviderType
    provider_id: Optional[str] = None
    snapshot_id: str = Field(min_length=1)
    discovered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())
    identified_platform_type: PlatformType = PlatformType.UNKNOWN

    physicals: list[Physical] = Field(default_factory=list)
    os_entities: list[OS] = Field(default_factory=list)
    platforms: list[Platform] = Field(default_factory=list)
    clusters: list[Cluster] = Field(default_factory=list)
    nodes: list[Node] = Field(default_factory=list)
    execution_environments: list[ExecutionEnvironment] = Field(default_factory=list)
    workloads: list[Workload] = Field(default_factory=list)
    networks: list[Network] = Field(default_factory=list)
    storages: list[Storage] = Field(default_factory=list)
    accelerators: list[Accelerator] = Field(default_factory=list)
    relationship_evidence: list[RawRelationshipEvidence] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @property
    def entity_count(self) -> int:
        return (len(self.physicals) + len(self.os_entities)
                + len(self.platforms) + len(self.clusters) + len(self.nodes)
                + len(self.execution_environments) + len(self.workloads)
                + len(self.networks) + len(self.storages) + len(self.accelerators))

    @property
    def is_empty(self) -> bool:
        return self.entity_count == 0

    @classmethod
    def from_normalization(
        cls, result: NormalizationResult,
        provider_id: Optional[str] = None,
    ) -> "CanonicalInventory":
        """Build inventory from NormalizationResult — the ONLY conversion path."""
        identified = PlatformType.UNKNOWN
        if result.platforms:
            identified = result.platforms[0].platform_type
        return cls(
            provider_type=result.provider_type,
            provider_id=provider_id,
            snapshot_id=result.snapshot_id,
            identified_platform_type=identified,
            physicals=list(result.physicals),
            os_entities=list(result.os_entities),
            platforms=list(result.platforms),
            clusters=list(result.clusters),
            nodes=list(result.nodes),
            execution_environments=list(result.execution_environments),
            workloads=list(result.workloads),
            networks=list(result.networks),
            storages=list(result.storages),
            accelerators=list(result.accelerators),
            relationship_evidence=list(result.relationship_evidence),
        )


class DiscoveryResult(BaseModel):
    """Result of a platform discovery run.

    Wraps the existing adapter → normalizer pipeline into a single
    discovery-level result.

    Discovery status semantics:
        SUCCESS:  Collection + normalization succeeded
        PARTIAL:  Some capabilities succeeded, some failed
        FAILED:   Discovery itself failed (auth, connection, etc.)
        SKIPPED:  External preconditions not met (e.g., no credentials)
    """

    provider_type: ProviderType
    provider_id: Optional[str] = None
    discovery_status: OrchestrationStatus = OrchestrationStatus.FAILED

    snapshot_id: str = Field(min_length=1)
    collected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())
    identified_platform_type: PlatformType = PlatformType.UNKNOWN

    inventory: Optional[CanonicalInventory] = None

    capabilities_attempted: list[AdapterCapability] = Field(default_factory=list)
    capabilities_succeeded: list[AdapterCapability] = Field(default_factory=list)
    capabilities_failed: list[AdapterCapability] = Field(default_factory=list)

    relationship_evidence: list[RawRelationshipEvidence] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @property
    def is_success(self) -> bool:
        return self.discovery_status == OrchestrationStatus.SUCCESS

    @property
    def is_partial(self) -> bool:
        return self.discovery_status == OrchestrationStatus.PARTIAL

    @property
    def is_skipped(self) -> bool:
        return self.discovery_status == OrchestrationStatus.SKIPPED

    @property
    def is_failed(self) -> bool:
        return self.discovery_status == OrchestrationStatus.FAILED

    @property
    def entity_count(self) -> int:
        if self.inventory is None:
            return 0
        return self.inventory.entity_count

