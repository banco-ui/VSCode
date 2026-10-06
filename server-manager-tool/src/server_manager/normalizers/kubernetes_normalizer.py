"""Kubernetes Provider Normalizer — Phase 13G-4.

Transforms Kubernetes RawProviderSnapshot → Canonical Domain Model entities.

    RawProviderSnapshot (K8s raw data)
        ↓
    KubernetesProviderNormalizer
        ↓
    Canonical Domain Model (Platform, Cluster, Node,
                            ExecutionEnvironment, Network, Storage)

Architecture:
    Inherits from GenericProviderNormalizer to reuse entity creation,
    enum mapping, ref resolution, and status determination.
    Overrides normalize() to transform K8s raw payload → generic payload
    format, then delegates to super().normalize().

K8s → Canonical mapping (deterministic, no inference):

    K8s Cluster   → Platform(KUBERNETES) + Cluster(KUBERNETES)
    K8s Node      → Node (provider_id = node name)
    K8s Pod       → ExecutionEnvironment(POD)
    K8s Container → ExecutionEnvironment(CONTAINER)
    K8s Service   → Network(VIRTUAL)
    K8s PV        → Storage(PV)
    K8s PVC       → Storage(PVC)

NOT created (conservative — no explicit evidence):
    - Physical (K8s API does not provide hardware identity)
    - OS (K8s API does not provide host OS info)
    - Workload (Deployments/StatefulSets/DaemonSets are not
      automatically canonical Workloads — requires explicit rule)
    - Accelerator (device plugin info is not sufficient evidence)

Relationship evidence preserved from snapshot:
    - Pod → Node (DIRECT, from spec.nodeName)
    - Pod → Container (DERIVED, from spec.containers[])
"""
from __future__ import annotations

import logging
from typing import Any

from ..models.canonical import ProviderType
from ..providers.base import RawProviderSnapshot
from .provider_normalizer import GenericProviderNormalizer, NormalizationResult

logger = logging.getLogger(__name__)


class KubernetesProviderNormalizer(GenericProviderNormalizer):
    """Kubernetes-specific provider normalizer.

    Transforms Kubernetes RawProviderSnapshot into canonical entities by:
    1. Transforming K8s raw payload → generic payload format
    2. Delegating to GenericProviderNormalizer.normalize()

    This reuses all existing infrastructure:
    - CanonicalIdentityGenerator for canonical IDs
    - _make_source_evidence for provenance
    - _map_enum for enum mapping
    - _resolve_all_refs for ref resolution
    - _determine_status for result status

    K8s → Canonical mapping rules (deterministic, no inference):

    Platform:
        K8s cluster info → Platform(platform_type=KUBERNETES, version=...)
        ProviderType.KUBERNETES → PlatformType.KUBERNETES (explicit)

    Cluster:
        K8s cluster info → Cluster(cluster_type=KUBERNETES)

    Node:
        K8s Node → Node(name=node_name, cluster_ref=cluster_pid)
        provider_id = Node metadata.name (referenced by Pod.spec.nodeName)

    Pod:
        K8s Pod → ExecutionEnvironment(ee_type=POD, name=pod_name)
        provider_id = Pod metadata.uid (or name fallback)
        node_ref = Pod.spec.nodeName (if present)

    Container:
        Pod.spec.containers[] → ExecutionEnvironment(ee_type=CONTAINER)
        provider_id = f"{pod_uid}/{container_name}"

    Service:
        K8s Service → Network(network_type=VIRTUAL, name=service_name)
        Raw K8s Service preserved in metadata.kubernetes

    PV:
        K8s PV → Storage(storage_type=PV, name=pv_name)

    PVC:
        K8s PVC → Storage(storage_type=PVC, name=pvc_name)

    NOT created:
        - Physical (no hardware identity from K8s API)
        - OS (no host OS info from K8s API)
        - Workload (Deployments/StatefulSets/DaemonSets need explicit rule)
        - Accelerator (device plugin info is insufficient)
    """

    def __init__(self) -> None:
        super().__init__(ProviderType.KUBERNETES)

    def normalize(self, snapshot: RawProviderSnapshot) -> NormalizationResult:
        """Normalize a Kubernetes snapshot into canonical entities.

        Transforms K8s raw payload → generic payload format, then
        delegates to GenericProviderNormalizer.normalize().

        Args:
            snapshot: RawProviderSnapshot with K8s raw data in payload.

        Returns:
            NormalizationResult with canonical entities.
        """
        generic_payload = self._transform_k8s_to_generic(snapshot)

        generic_snapshot = RawProviderSnapshot(
            snapshot_id=snapshot.snapshot_id,
            provider_type=snapshot.provider_type,
            provider_id=snapshot.provider_id,
            collected_at=snapshot.collected_at,
            collection_status=snapshot.collection_status,
            declared_capabilities=snapshot.declared_capabilities,
            capability_results=snapshot.capability_results,
            payload=generic_payload,
            relationship_evidence=snapshot.relationship_evidence,
            source_evidence=snapshot.source_evidence,
            errors=list(snapshot.errors),
            warnings=list(snapshot.warnings),
        )

        return super().normalize(generic_snapshot)

    def _transform_k8s_to_generic(
        self, snapshot: RawProviderSnapshot,
    ) -> dict[str, Any]:
        """Transform Kubernetes raw payload to generic canonical payload.

        The GenericProviderNormalizer expects payload keys:
            platforms, clusters, nodes, execution_environments,
            workloads, networks, storages, accelerators, physicals, os

        Each item is a dict with provider_id and entity-specific fields.
        Refs are provider_id strings (resolved in second pass).

        K8s objects are preserved in metadata.kubernetes where appropriate.
        """
        payload = snapshot.payload
        cluster_info = payload.get("cluster", {})
        if not isinstance(cluster_info, dict):
            cluster_info = {}

        cluster_name = cluster_info.get("name", "k8s-cluster")
        cluster_uid = cluster_info.get("uid", cluster_name)
        k8s_version = cluster_info.get("version", "")
        platform_pid = f"platform-{cluster_uid}"
        cluster_pid = f"cluster-{cluster_uid}"

        generic: dict[str, Any] = {
            "platforms": [],
            "clusters": [],
            "nodes": [],
            "execution_environments": [],
            "workloads": [],
            "networks": [],
            "storages": [],
            "accelerators": [],
            "physicals": [],
            "os": [],
        }

        # ── Platform: K8s cluster → Platform(KUBERNETES) ───────────
        generic["platforms"].append({
            "provider_id": platform_pid,
            "platform_type": "KUBERNETES",
            "version": k8s_version,
            "metadata": {
                "kubernetes": {
                    "cluster_name": cluster_name,
                    "cluster_uid": cluster_uid,
                },
            },
        })

        # ── Cluster: K8s cluster → Cluster(KUBERNETES) ──────────────
        generic["clusters"].append({
            "provider_id": cluster_pid,
            "cluster_type": "KUBERNETES",
            "platform_ref": platform_pid,
            "metadata": {
                "kubernetes": {
                    "cluster_name": cluster_name,
                    "cluster_uid": cluster_uid,
                },
            },
        })

        # ── Nodes: K8s Node → canonical Node ────────────────────────
        # provider_id = Node metadata.name (referenced by Pod.spec.nodeName)
        for node in payload.get("nodes", []):
            if not isinstance(node, dict):
                continue
            metadata = node.get("metadata", {})
            if not isinstance(metadata, dict):
                continue
            node_name = metadata.get("name", "")
            if not node_name:
                continue
            node_uid = metadata.get("uid", node_name)
            generic["nodes"].append({
                "provider_id": node_name,
                "name": node_name,
                "cluster_ref": cluster_pid,
                "metadata": {
                    "kubernetes": {
                        "uid": node_uid,
                        "labels": metadata.get("labels", {}),
                        "raw": node,
                    },
                },
            })

        # ── Pods → ExecutionEnvironment(POD) ────────────────────────
        # K8s Pod → EE(type=POD)
        # provider_id = Pod metadata.uid (or name)
        # node_ref = Pod.spec.nodeName (if present)
        for pod in payload.get("pods", []):
            if not isinstance(pod, dict):
                continue
            metadata = pod.get("metadata", {})
            if not isinstance(metadata, dict):
                continue
            pod_name = metadata.get("name", "")
            pod_uid = metadata.get("uid", "")
            pod_pid = pod_uid or pod_name
            if not pod_pid:
                continue

            spec = pod.get("spec", {})
            if not isinstance(spec, dict):
                spec = {}
            node_name = spec.get("nodeName")

            ee_item: dict[str, Any] = {
                "provider_id": pod_pid,
                "ee_type": "POD",
                "name": pod_name,
                "metadata": {
                    "kubernetes": {
                        "uid": pod_uid,
                        "namespace": metadata.get("namespace", ""),
                        "raw": pod,
                    },
                },
            }
            if node_name:
                ee_item["node_ref"] = node_name
            generic["execution_environments"].append(ee_item)

            # ── Containers → ExecutionEnvironment(CONTAINER) ───────
            containers = spec.get("containers", [])
            if isinstance(containers, list):
                for container in containers:
                    if not isinstance(container, dict):
                        continue
                    container_name = container.get("name", "")
                    if not container_name:
                        continue
                    container_pid = f"{pod_pid}/{container_name}"
                    generic["execution_environments"].append({
                        "provider_id": container_pid,
                        "ee_type": "CONTAINER",
                        "name": container_name,
                        "metadata": {
                            "kubernetes": {
                                "pod_uid": pod_uid,
                                "pod_name": pod_name,
                                "image": container.get("image", ""),
                                "raw": container,
                            },
                        },
                    })

        # ── Services → Network ─────────────────────────────────────
        # K8s Service → Network(network_type=VIRTUAL)
        for svc in payload.get("services", []):
            if not isinstance(svc, dict):
                continue
            metadata = svc.get("metadata", {})
            if not isinstance(metadata, dict):
                continue
            svc_name = metadata.get("name", "")
            svc_uid = metadata.get("uid", "")
            svc_pid = svc_uid or svc_name
            if not svc_pid:
                continue
            spec = svc.get("spec", {})
            if not isinstance(spec, dict):
                spec = {}
            generic["networks"].append({
                "provider_id": svc_pid,
                "network_type": "VIRTUAL",
                "name": svc_name,
                "metadata": {
                    "kubernetes": {
                        "uid": svc_uid,
                        "namespace": metadata.get("namespace", ""),
                        "service_type": spec.get("type", "ClusterIP"),
                        "cluster_ip": spec.get("clusterIP", ""),
                        "raw": svc,
                    },
                },
            })

        # ── PersistentVolumes → Storage(PV) ─────────────────────────
        for pv in payload.get("persistent_volumes", []):
            if not isinstance(pv, dict):
                continue
            metadata = pv.get("metadata", {})
            if not isinstance(metadata, dict):
                continue
            pv_name = metadata.get("name", "")
            pv_uid = metadata.get("uid", "")
            pv_pid = pv_uid or pv_name
            if not pv_pid:
                continue
            generic["storages"].append({
                "provider_id": pv_pid,
                "storage_type": "PV",
                "name": pv_name,
                "metadata": {
                    "kubernetes": {
                        "uid": pv_uid,
                        "raw": pv,
                    },
                },
            })

        # ── PersistentVolumeClaims → Storage(PVC) ───────────────────
        for pvc in payload.get("persistent_volume_claims", []):
            if not isinstance(pvc, dict):
                continue
            metadata = pvc.get("metadata", {})
            if not isinstance(metadata, dict):
                continue
            pvc_name = metadata.get("name", "")
            pvc_uid = metadata.get("uid", "")
            pvc_pid = pvc_uid or pvc_name
            if not pvc_pid:
                continue
            generic["storages"].append({
                "provider_id": pvc_pid,
                "storage_type": "PVC",
                "name": pvc_name,
                "metadata": {
                    "kubernetes": {
                        "uid": pvc_uid,
                        "namespace": metadata.get("namespace", ""),
                        "raw": pvc,
                    },
                },
            })

        # Deployments, StatefulSets, DaemonSets are NOT mapped to Workload.
        # They are preserved in the raw payload for future use.
        # No Physical, OS, Accelerator, or Workload entities are created.

        return generic
