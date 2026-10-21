"""Redfish Collector (Phase 2).

Collects hardware inventory data via Redfish API.
"""
from __future__ import annotations

import logging
import time
import urllib.error
from typing import Any, Optional

from .base import BaseCollector

logger = logging.getLogger(__name__)

# Phase 0.2: Retry configuration for resilient GET calls.
# Only idempotent GET requests are retried, and only on transient errors
# (connection errors, timeouts, 5xx server errors). 401/403/4xx and TLS
# verification failures are never retried.
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds
RETRY_BACKOFF_MAX = 10.0  # cap for a single backoff sleep
RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})


class RedfishCollector(BaseCollector):
    """Collect server hardware data via DMTF Redfish API."""

    def __init__(
        self,
        host: str,
        port: int = 443,
        username: str = "",
        password: str = "",
        use_ssl: bool = True,
        verify_ssl: bool = True,  # Phase 0.2: Default to True for security
        timeout: int = 30,
        ca_bundle: Optional[str] = None,  # Phase 1-RF.4: Optional CA bundle path
    ) -> None:
        super().__init__(host, port, username, password)
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.ca_bundle = ca_bundle  # Phase 1-RF.4: Store CA bundle path

    @property
    def source_name(self) -> str:
        return "redfish"

    @property
    def base_url(self) -> str:
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}:{self.port}"

    def collect(self) -> dict[str, Any]:
        """Collect Redfish data.

        Returns:
            Dict with raw Redfish data including:
            - System info
            - Processor info
            - Memory info
            - Storage info
            - Network info
            - Power/Thermal info
        """
        # Import urllib here to avoid hard dependency at module level
        import json
        import urllib.request

        data: dict[str, Any] = {
            "source": "redfish",
            "endpoint": self.base_url,
        }

        # Fetch root
        root = self._get("/redfish/v1/")
        if root is None:
            raise ConnectionError(f"Failed to connect to Redfish at {self.base_url}")

        data["redfish_version"] = root.get("RedfishVersion", "unknown")

        # Fetch systems
        systems_data = self._get_collection(root, "Systems")
        if systems_data:
            system = self._get_first_member(systems_data)
            if system:
                data["system"] = system
                # Processors
                proc_data = self._get_collection(system, "Processors")
                if proc_data:
                    data["processors"] = self._get_all_members(proc_data)
                # Memory
                mem_data = self._get_collection(system, "Memory")
                if mem_data:
                    data["memory"] = self._get_all_members(mem_data)
                # Network interfaces
                net_data = self._get_collection(system, "NetworkInterfaces")
                if net_data:
                    data["network_interfaces"] = self._get_all_members(net_data)
                # PCIe devices
                pcie_data = self._get_collection(system, "PCIeDevices")
                if pcie_data:
                    data["pcie_devices"] = self._get_all_members(pcie_data)
                # Storage
                storage_data = self._get_collection(system, "Storage")
                if storage_data:
                    data["storage"] = self._collect_storage(storage_data)

        # Fetch chassis

        chassis_data = self._get_collection(root, "Chassis")
        if chassis_data:
            chassis = self._get_first_member(chassis_data)
            if chassis:
                data["chassis"] = chassis
                # Power
                power = self._get_from_ref(chassis, "Power")
                if power:
                    data["power"] = power
                # Thermal
                thermal = self._get_from_ref(chassis, "Thermal")
                if thermal:
                    data["thermal"] = thermal

        # Fetch managers (iDRAC/iLO)
        managers_data = self._get_collection(root, "Managers")
        if managers_data:
            manager = self._get_first_member(managers_data)
            if manager:
                data["manager"] = manager

        return data

    def _get_with_retry(self, path: str) -> Optional[dict[str, Any]]:
        """Make a GET request with limited retry on transient errors.

        Phase 0.2: Retry only on connection errors, timeouts, and 5xx server errors.
        Never retry on 401/403/4xx client errors or TLS verification failures.

        Phase 1-RF.4.2: Explicitly exclude CA bundle errors (FileNotFoundError,
        ValueError) and TLS/SSL errors from retry. Check URLError.reason for
        wrapped SSL errors.
        """
        import ssl
        import json

        last_exc: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                return self._get_once(path)
            except urllib.error.HTTPError as e:
                # Don't retry client errors (401/403/4xx) or TLS errors
                if e.code < 500:
                    logger.error("Redfish GET %s failed with %d (no retry)", path, e.code)
                    return None
                # Retry 5xx server errors
                if e.code in RETRYABLE_STATUS_CODES:
                    if attempt < MAX_RETRIES - 1:
                        backoff = min(RETRY_BACKOFF_BASE * (2 ** attempt), RETRY_BACKOFF_MAX)
                        logger.warning(
                            "Redfish GET %s failed with %d, retrying in %.1fs (attempt %d/%d)",
                            path, e.code, backoff, attempt + 1, MAX_RETRIES
                        )
                        time.sleep(backoff)
                    else:
                        logger.error("Redfish GET %s failed with %d after %d retries", path, e.code, MAX_RETRIES)
                        return None
                else:
                    logger.error("Redfish GET %s failed with %d (no retry)", path, e.code)
                    return None
            except urllib.error.URLError as e:
                # Phase 1-RF.4.2: Check if URLError wraps an SSL error
                if isinstance(e.reason, (ssl.SSLError, ssl.SSLCertVerificationError)):
                    logger.error("Redfish GET %s TLS error (no retry): %s", path, e.reason)
                    return None
                # URLError with other reasons (DNS, connection refused) -> retry
                if attempt < MAX_RETRIES - 1:
                    backoff = min(RETRY_BACKOFF_BASE * (2 ** attempt), RETRY_BACKOFF_MAX)
                    logger.warning(
                        "Redfish GET %s connection error, retrying in %.1fs (attempt %d/%d)",
                        path, backoff, attempt + 1, MAX_RETRIES
                    )
                    time.sleep(backoff)
                else:
                    logger.error("Redfish GET %s failed after %d retries: %s", path, MAX_RETRIES, e.reason)
                    return None
            except (ssl.SSLError, ssl.SSLCertVerificationError) as e:
                # Phase 1-RF.4.2: Direct SSL errors - never retry
                logger.error("Redfish GET %s TLS error (no retry): %s", path, e)
                return None
            except json.JSONDecodeError as e:
                # Phase 1-RF.9: Malformed response body — JSON parse error,
                # not a retryable condition. Must precede the ValueError
                # branch (JSONDecodeError subclasses ValueError).
                logger.error("Redfish GET %s JSON parse error (no retry): %s", path, e)
                return None
            except (FileNotFoundError, ValueError) as e:
                # Phase 1-RF.4.2: CA bundle config errors - never retry
                logger.error("Redfish GET %s CA bundle error (no retry): %s", path, e)
                return None
            except (TimeoutError, ConnectionError, OSError) as e:
                # Retry connection errors and timeouts
                if attempt < MAX_RETRIES - 1:
                    backoff = min(RETRY_BACKOFF_BASE * (2 ** attempt), RETRY_BACKOFF_MAX)
                    logger.warning(
                        "Redfish GET %s connection error, retrying in %.1fs (attempt %d/%d)",
                        path, backoff, attempt + 1, MAX_RETRIES
                    )
                    time.sleep(backoff)
                else:
                    logger.error("Redfish GET %s failed after %d retries: %s", path, MAX_RETRIES, e)
                    return None
            except Exception as e:
                # Unknown errors: don't retry, just log and return None
                logger.error("Redfish GET %s failed: %s", path, e)
                return None
        return None

    def _get_once(self, path: str) -> Optional[dict[str, Any]]:
        """Make a single GET request without retry."""
        import base64
        import os
        import urllib.request

        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")

        if self.username and self._password:
            creds = base64.b64encode(f"{self.username}:{self._password}".encode()).decode()
            req.add_header("Authorization", f"Basic {creds}")

        # Phase 1-RF.4: TLS context with optional CA bundle
        import ssl
        ctx = ssl.create_default_context()
        
        # Phase 1-RF.4: Load CA bundle if specified
        if self.ca_bundle:
            if not os.path.exists(self.ca_bundle):
                raise FileNotFoundError(f"CA bundle not found: {self.ca_bundle}")
            if not os.path.isfile(self.ca_bundle):
                raise ValueError(f"CA bundle path is not a file: {self.ca_bundle}")
            try:
                ctx.load_verify_locations(cafile=self.ca_bundle)
            except ssl.SSLError as e:
                raise ValueError(f"Invalid CA bundle file: {self.ca_bundle} - {e}")
        elif not self.verify_ssl:
            # Phase 0.2: Disable TLS verification only if verify_ssl=False and no CA bundle
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                import json
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.error("Redfish GET %s failed: %s", path, e)
            raise
        except Exception as e:
            logger.error("Redfish GET %s failed: %s", path, e)
            raise

    def _get(self, path: str) -> Optional[dict[str, Any]]:
        """Make a GET request to the Redfish API (with retry)."""
        return self._get_with_retry(path)

    def _get_collection(self, parent: dict, key: str) -> Optional[dict]:
        """Get a collection reference from a parent object."""
        ref = parent.get(key)
        if ref is None:
            return None
        if isinstance(ref, dict) and "@odata.id" in ref:
            return self._get(ref["@odata.id"])
        return ref

    def _get_from_ref(self, parent: dict, key: str) -> Optional[dict]:
        """Get a resource from a reference in parent."""
        ref = parent.get(key)
        if ref is None:
            return None
        if isinstance(ref, dict) and "@odata.id" in ref:
            return self._get(ref["@odata.id"])
        return ref

    def _get_first_member(self, collection: dict) -> Optional[dict]:
        """Get the first member of a collection."""
        members = collection.get("Members", [])
        if not members:
            return None
        first = members[0]
        if isinstance(first, dict) and "@odata.id" in first:
            return self._get(first["@odata.id"])
        return first

    def _get_all_members(self, collection: dict) -> list[dict]:
        """Get all members of a collection."""
        members = collection.get("Members", [])
        results = []
        # P1-RF.12: collection identifier for skip warnings. The collection's
        # own @odata.id is a standard Redfish URI — safe to log. Member payload
        # is never logged (could contain sensitive attributes).
        collection_id = collection.get("@odata.id", "unknown collection")
        for m in members:
            if isinstance(m, dict) and "@odata.id" in m:
                data = self._get(m["@odata.id"])
                if data:
                    results.append(data)
                else:
                    # P1-RF.15: A falsy fetch result (e.g. 404/TLS/JSON error —
                    # _get_with_retry returns None) is skipped (unchanged) but
                    # now warned. Logs standard Redfish URIs only — never
                    # member payload, serials or credentials.
                    logger.warning(
                        "Redfish collection %s: failed to fetch member %s",
                        collection_id,
                        m.get("@odata.id"),
                    )
            else:
                # A member without @odata.id cannot be fetched — skipped
                # (unchanged behavior). Warn so the skip is traceable without
                # exposing member data.
                logger.warning(
                    "Redfish collection %s: skipping member without @odata.id",
                    collection_id,
                )
        return results

    def _collect_storage(self, storage_collection: dict) -> list[dict]:
        """Collect storage resources from a Storage collection.

        Fetches each Storage member, along with its Drives and Volumes.
        Partial failures are logged and skipped — one storage subsystem
        failure does not prevent collection of others.

        Args:
            storage_collection: The Storage collection response.

        Returns:
            List of storage resource dicts, each containing:
            - controller info (StorageControllers)
            - drives (list of drive dicts)
            - volumes (list of volume dicts)
        """
        results: list[dict] = []
        members = storage_collection.get("Members", [])
        for m in members:
            if not isinstance(m, dict) or "@odata.id" not in m:
                continue
            storage = self._get(m["@odata.id"])
            if storage is None:
                logger.warning("Failed to fetch Storage resource at %s", m.get("@odata.id"))
                continue

            entry: dict[str, Any] = {
                "@odata.id": storage.get("@odata.id", m["@odata.id"]),
                "controllers": storage.get("StorageControllers", []),
            }

            # Collect Drives
            drives_ref = storage.get("Drives")
            if drives_ref and isinstance(drives_ref, list):
                drives: list[dict] = []
                for d in drives_ref:
                    if isinstance(d, dict) and "@odata.id" in d:
                        drive = self._get(d["@odata.id"])
                        if drive:
                            drives.append(drive)
                        else:
                            logger.warning("Failed to fetch Drive at %s", d.get("@odata.id"))
                entry["drives"] = drives
            else:
                entry["drives"] = []

            # Collect Volumes
            volumes_ref = storage.get("Volumes")
            if isinstance(volumes_ref, dict) and "@odata.id" in volumes_ref:
                vol_collection = self._get(volumes_ref["@odata.id"])
                if vol_collection:
                    volumes: list[dict] = []
                    for v in vol_collection.get("Members", []):
                        if isinstance(v, dict) and "@odata.id" in v:
                            vol = self._get(v["@odata.id"])
                            if vol:
                                volumes.append(vol)
                            else:
                                logger.warning("Failed to fetch Volume at %s", v.get("@odata.id"))
                    entry["volumes"] = volumes
                else:
                    entry["volumes"] = []
            else:
                entry["volumes"] = []

            results.append(entry)

        return results


