"""Provider Adapter + Raw Snapshot Contract — Phase 13G-2.

This module implements the provider discovery/collection boundary:

    Provider
       ↓
    ProviderAdapter
       ↓
    RawProviderSnapshot
       ↓
    [Phase 13G-3: ProviderNormalizer → Canonical Domain Model]

Architecture boundaries:
    ProviderAdapter  ≠  Collector  ≠  Normalizer  ≠  Verifier
    ProviderAdapter  ≠  Store  ≠  Orchestrator

ProviderAdapter responsibilities:
    1. Provider identity
    2. Provider capability declaration
    3. Provider-specific collection (may compose existing BaseCollector)
    4. Raw data capture
    5. Collection status
    6. Source/provenance metadata
    7. Partial/error information

ProviderAdapter does NOT:
    ❌ Create canonical entities (Normalizer's job — Phase 13G-3)
    ❌ Create canonical relationships
    ❌ Infer business semantics
    ❌ Perform verification
    ❌ Persist data
    ❌ Orchestrate workflows

Reused from existing codebase:
    - ProviderType, SourceEvidence, RelationshipEvidenceType (models.canonical)
    - OrchestrationStatus, ErrorCategory (orchestrator.models)
    - Confidence (models.enums)

New in this phase:
    - AdapterCapability (enum)
    - CapabilityResult (model)
    - RawRelationshipEvidence (model)
    - RawProviderSnapshot (model)
    - ProviderAdapter (ABC)

Dependency note:
    This module imports OrchestrationStatus and ErrorCategory from
    orchestrator.models. While this creates a providers → orchestrator
    dependency (architecturally suboptimal since orchestrator is the
    highest-level module), the spec requires reusing these existing
    enums and prohibits creating duplicates. Future refactoring could
    move shared enums to a common module.
"""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from ..models.canonical import (
    ProviderType,
    RelationshipEvidenceType,
    SourceEvidence,
)
from ..orchestrator.models import ErrorCategory, OrchestrationStatus

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
#  CAPABILITY ENUM
# ════════════════════════════════════════════════════════════════════════


class AdapterCapability(str, Enum):
    """Discovery capabilities a provider adapter can declare.

    Capabilities declare what an adapter CAN collect, NOT what WAS collected.
    Declaring a capability does not guarantee the provider data contains
    corresponding entities.

    The first 10 values mirror the 13G-1 canonical entity domains.
    Additional values cover cross-cutting concerns.
    """
    PHYSICAL = "PHYSICAL"
    OS = "OS"
    PLATFORM = "PLATFORM"
    CLUSTER = "CLUSTER"
    NODE = "NODE"
    EXECUTION_ENVIRONMENT = "EXECUTION_ENVIRONMENT"
    WORKLOAD = "WORKLOAD"
    NETWORK = "NETWORK"
    STORAGE = "STORAGE"
    ACCELERATOR = "ACCELERATOR"
    RELATIONSHIP_DISCOVERY = "RELATIONSHIP_DISCOVERY"
    METRICS = "METRICS"
    EVENTS = "EVENTS"
    HEALTH = "HEALTH"


# ════════════════════════════════════════════════════════════════════════
#  CAPABILITY RESULT
# ════════════════════════════════════════════════════════════════════════


class CapabilityResult(BaseModel):
    """Result of collecting a single capability.

    Captures the per-capability collection status, allowing partial
    collection to be represented:

        Cluster = SUCCESS
        Node = SUCCESS
        Workload = PARTIAL
        Network = FAILED

    Partial != Empty, Partial != Success, Partial != Verification failure.
    """
    capability: AdapterCapability
    status: OrchestrationStatus = OrchestrationStatus.FAILED
    data: Optional[dict[str, Any]] = None
    errors: list[str] = Field(default_factory=list)
    error_category: Optional[ErrorCategory] = None
    warnings: list[str] = Field(default_factory=list)
    item_count: int = 0
    collected_at: Optional[str] = None

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  RAW RELATIONSHIP EVIDENCE
# ════════════════════════════════════════════════════════════════════════


class RawRelationshipEvidence(BaseModel):
    """Raw relationship evidence from provider data.

    Represents a relationship that the provider explicitly states (DIRECT)
    or that can be directly computed from provider data without inference
    (DERIVED).

    This is RAW evidence — the Normalizer (Phase 13G-3) will create
    canonical relationships from this evidence.

    INFERRED and UNKNOWN evidence types are NOT allowed.
    RelationshipEvidenceType enum only has DIRECT and DERIVED.
    LLM-based, heuristic, similarity-based discovery is prohibited.

    Example:
        Kubernetes Pod spec contains spec.nodeName → DIRECT evidence
        that Pod X runs on Node Y.

    Identity note:
        source_entity_ref and target_entity_ref are PROVIDER-SIDE
        references (provider_id), NOT canonical_id. The Normalizer
        will resolve these to canonical entities.
    """
    source_entity_ref: str = Field(min_length=1)
    target_entity_ref: str = Field(min_length=1)
    relationship_type: str = Field(min_length=1)
    evidence_type: RelationshipEvidenceType = RelationshipEvidenceType.DIRECT
    raw_data: Optional[dict[str, Any]] = None

    model_config = {"extra": "forbid"}


# ════════════════════════════════════════════════════════════════════════
#  RAW PROVIDER SNAPSHOT
# ════════════════════════════════════════════════════════════════════════


class RawProviderSnapshot(BaseModel):
    """Raw provider snapshot — provider-originated data preservation boundary.

    Captures raw data from a single provider collection run. This is NOT
    a canonical model — it preserves provider-specific data structures
    as-is (Kubernetes JSON, Redfish JSON, WRCP CLI output, etc.).

    Identity model:
        snapshot_id:   unique ID for this collection result
        provider_id:   provider's entity identity (NOT canonical_id)
        canonical_id:  NOT generated in this phase (Phase 13G-3 assigns it)

    The snapshot does NOT contain canonical entities. It contains raw
    provider data that the Normalizer will transform into canonical
    entities in Phase 13G-3.

    Raw payload boundary:
        The `payload` field is the ONLY place where untyped
        dict[str, Any] raw data is allowed. This confines provider
        heterogeneity to a single boundary.

    Partial collection:
        Per-capability results in `capability_results` allow partial
        collection to be represented. `collection_status` is the
        overall status derived from capability results.
    """
    snapshot_id: str = Field(min_length=1)
    provider_type: ProviderType
    provider_id: Optional[str] = None
    collected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Overall collection status (reused from orchestrator.models)
    collection_status: OrchestrationStatus = OrchestrationStatus.FAILED

    # Declared capabilities (what this adapter CAN collect)
    declared_capabilities: list[AdapterCapability] = Field(default_factory=list)

    # Per-capability results (allows partial collection representation)
    capability_results: list[CapabilityResult] = Field(default_factory=list)

    # Raw payload — provider-specific data preserved as-is
    # This is the ONLY boundary for untyped raw data
    payload: dict[str, Any] = Field(default_factory=dict)

    # Raw relationship evidence (DIRECT or DERIVED only)
    relationship_evidence: list[RawRelationshipEvidence] = Field(default_factory=list)

    # Provenance (reused from canonical.SourceEvidence)
    source_evidence: Optional[SourceEvidence] = None

    # Overall errors and warnings
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @field_validator("snapshot_id")
    @classmethod
    def snapshot_id_non_empty(cls, v: str) -> str:
        """Ensure snapshot_id is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("snapshot_id must not be empty")
        return v

    @property
    def successful_capabilities(self) -> list[AdapterCapability]:
        """Capabilities that were collected successfully."""
        return [
            cr.capability
            for cr in self.capability_results
            if cr.status == OrchestrationStatus.SUCCESS
        ]

    @property
    def failed_capabilities(self) -> list[AdapterCapability]:
        """Capabilities that failed collection."""
        return [
            cr.capability
            for cr in self.capability_results
            if cr.status == OrchestrationStatus.FAILED
        ]

    @property
    def partial_capabilities(self) -> list[AdapterCapability]:
        """Capabilities with partial collection."""
        return [
            cr.capability
            for cr in self.capability_results
            if cr.status == OrchestrationStatus.PARTIAL
        ]

    @property
    def is_partial(self) -> bool:
        """True if any capability partially succeeded."""
        return any(
            cr.status == OrchestrationStatus.PARTIAL
            for cr in self.capability_results
        )


# ════════════════════════════════════════════════════════════════════════
#  PROVIDER ADAPTER (ABC)
# ════════════════════════════════════════════════════════════════════════


class ProviderAdapter(ABC):
    """Abstract base class for provider adapters.

    A ProviderAdapter is the provider-specific discovery/collection boundary.
    It declares capabilities, collects raw data, and returns a
    RawProviderSnapshot.

    The ProviderAdapter MAY compose existing BaseCollector instances
    for protocol-level collection (Redfish, SSH, etc.). It does NOT
    replace them — it adds:
      - Provider identity (ProviderType)
      - Capability declaration
      - RawProviderSnapshot output (structured, with provenance)
      - Per-capability status tracking
      - Error categorization

    The ProviderAdapter does NOT:
      ❌ Create canonical entities (Normalizer's job — Phase 13G-3)
      ❌ Create canonical relationships
      ❌ Infer business semantics ("this is probably a Workload")
      ❌ Perform LLM/heuristic interpretation
      ❌ Verify data
      ❌ Persist data
      ❌ Orchestrate workflows

    Identity separation:
        provider_type:   which provider (KUBERNETES, WRCP, REDFISH, etc.)
        provider_id:     provider's identity for this target
        canonical_id:    NOT generated here (Phase 13G-3)
    """

    def __init__(
        self,
        provider_type: ProviderType,
        provider_id: Optional[str] = None,
    ) -> None:
        self._provider_type = provider_type
        self._provider_id = provider_id

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type for this adapter."""
        return self._provider_type

    @property
    def provider_id(self) -> Optional[str]:
        """Return the provider's identity for this target."""
        return self._provider_id

    @abstractmethod
    def capabilities(self) -> list[AdapterCapability]:
        """Declare what this adapter can collect.

        Returns:
            List of capabilities this adapter supports. This is a
            declaration of what CAN be collected, NOT what WAS collected.
            Declaring a capability does not guarantee the provider data
            contains corresponding entities.
        """
        ...

    @abstractmethod
    def collect(self, **kwargs: Any) -> RawProviderSnapshot:
        """Collect raw data from the provider.

        Returns:
            RawProviderSnapshot containing raw provider data.
            The snapshot may be partial — per-capability results
            indicate success/failure for each capability.

        Raises:
            May raise exceptions for connection failures.
            Use collect_safe() for error-handled collection.
        """
        ...

    def collect_safe(self, **kwargs: Any) -> RawProviderSnapshot:
        """Collect with error handling.

        Returns a RawProviderSnapshot with FAILED status if collection
        raises an exception. Per-capability errors are captured in
        the snapshot.

        This method mirrors BaseCollector.safe_collect() but returns
        a structured RawProviderSnapshot instead of a CollectionResult.
        """
        snapshot_id = f"snap-{uuid.uuid4().hex[:12]}"
        try:
            snapshot = self.collect(**kwargs)
            return snapshot
        except Exception as e:
            error_cat = ErrorCategory.from_exception(e)
            logger.error(
                "%s collection failed (%s): %s",
                self._provider_type.value,
                error_cat.value,
                e,
            )
            return RawProviderSnapshot(
                snapshot_id=snapshot_id,
                provider_type=self._provider_type,
                provider_id=self._provider_id,
                collection_status=OrchestrationStatus.FAILED,
                errors=[
                    f"[{self._provider_type.value}] Collection failed "
                    f"({error_cat.value}): {e}"
                ],
            )

