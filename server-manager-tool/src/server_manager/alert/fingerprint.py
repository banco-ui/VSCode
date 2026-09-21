"""Alert Fingerprint — Phase 11C.

Deterministic fingerprint generation for alert deduplication.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional


def create_fingerprint(
    server_id: str,
    alert_type: str,
    resource_type: str,
    resource_id: Optional[str],
    condition: str,
    version: int = 1,
) -> str:
    """Create a deterministic fingerprint for alert deduplication.
    
    Uses canonical JSON (sorted keys, no whitespace) encoded as UTF-8,
    then SHA-256 hash to produce a 64-character hexadecimal string.
    
    Args:
        server_id: Server identifier.
        alert_type: Alert classification (e.g., "HEALTH_CRITICAL").
        resource_type: Resource type (e.g., "system", "storage_controller").
        resource_id: Resource identifier (optional, None becomes "").
        condition: Condition expression (e.g., "health == CRITICAL").
        version: Fingerprint algorithm version (default: 1).
    
    Returns:
        64-character hexadecimal SHA-256 hash string.
    
    Example:
        >>> fp = create_fingerprint(
        ...     server_id="srv01",
        ...     alert_type="HEALTH_CRITICAL",
        ...     resource_type="system",
        ...     resource_id=None,
        ...     condition="health == CRITICAL"
        ... )
        >>> len(fp)
        64
    """
    # Normalize resource_id: None → ""
    normalized_resource_id = resource_id if resource_id is not None else ""
    
    # Build canonical input (keys will be sorted)
    data = {
        "alert_type": alert_type,
        "condition": condition,
        "resource_id": normalized_resource_id,
        "resource_type": resource_type,
        "server_id": server_id,
        "version": version,
    }
    
    # Canonical JSON: sorted keys, no whitespace
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    
    # SHA-256 hash
    hash_bytes = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    
    return hash_bytes


def validate_fingerprint(fingerprint: str) -> bool:
    """Validate fingerprint format.
    
    Args:
        fingerprint: Fingerprint string to validate.
    
    Returns:
        True if valid 64-character hexadecimal string.
    """
    if len(fingerprint) != 64:
        return False
    
    try:
        int(fingerprint, 16)
        return True
    except ValueError:
        return False
