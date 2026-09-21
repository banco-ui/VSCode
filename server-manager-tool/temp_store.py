"""AlertStore — SQLite persistence for alerts — Phase 11C.

Atomic lifecycle transitions, active deduplication, lock retry.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .models import Alert, AlertStatus, AlertSeverity, AlertType, ResourceType
from .fingerprint import create_fingerprint, validate_fingerprint

logger = logging.getLogger(__name__)

ALERT_STORE_SCHEMA_SQL = """
-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    -- Identity
    alert_id              TEXT PRIMARY KEY,
    fingerprint           TEXT NOT NULL,
    fingerprint_version   INTEGER NOT NULL DEFAULT 1,
    
    -- Server reference
    server_id             TEXT NOT NULL,
    
    -- Alert classification
    alert_type            TEXT NOT NULL,
    resource_type         TEXT NOT NULL,
    resource_id           TEXT,
    condition             TEXT NOT NULL,
    
    -- Severity
    severity              TEXT NOT NULL,
    
    -- Lifecycle
    status                TEXT NOT NULL,
    created_at            TEXT NOT NULL,
    updated_at            TEXT NOT NULL,
    acknowledged_at       TEXT,
    acknowledged_by       TEXT,
    acknowledge_note      TEXT,
    resolved_at           TEXT,
    resolution_note       TEXT,
    
    -- Threshold tracking
    consecutive_failure_count  INTEGER NOT NULL DEFAULT 0,
    consecutive_ok_count       INTEGER NOT NULL DEFAULT 0,
    
    -- References
    first_snapshot_id     TEXT,
    last_snapshot_id      TEXT,
    
    -- Metadata
    recovery_count        INTEGER NOT NULL DEFAULT 0,
    metadata_json         TEXT NOT NULL DEFAULT '{}'
);

-- Index for fingerprint lookup (deduplication)
CREATE INDEX IF NOT EXISTS idx_alerts_fingerprint ON alerts(fingerprint);

-- Index for status filtering (active alerts)
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);

-- Index for server filtering
CREATE INDEX IF NOT EXISTS idx_alerts_server_id ON alerts(server_id);

-- Index for severity filtering
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- Composite index: active alerts by server
CREATE INDEX IF NOT EXISTS idx_alerts_status_server ON alerts(status, server_id);

-- Index for created timestamp (sorting, pagination)
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);

-- Index for fingerprint lookup (deduplication - application level)
CREATE INDEX IF NOT EXISTS idx_alerts_fingerprint ON alerts(fingerprint);
"""

# SQLite lock retry configuration (matches SchedulerStore pattern)
DEFAULT_LOCK_RETRY_COUNT = 3
DEFAULT_LOCK_RETRY_BACKOFF = 0.1  # seconds


class AlertStoreError(Exception):
    """Base exception for AlertStore errors."""
    pass


class AlertNotFoundError(AlertStoreError):
    """Alert not found."""
    pass


class AlertDuplicateError(AlertStoreError):
    """Active alert with same fingerprint already exists."""
    pass


class AlertInvalidTransitionError(AlertStoreError):
    """Invalid lifecycle transition attempted."""
    pass

class AlertStore:
    """SQLite-backed alert persistence store."""
    
    def __init__(
        self,
        db_path: str | Path = ":memory:",
        lock_retry_count: int = DEFAULT_LOCK_RETRY_COUNT,
        lock_retry_backoff: float = DEFAULT_LOCK_RETRY_BACKOFF,
    ) -> None:
        self.db_path = str(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock_retry_count = lock_retry_count
        self._lock_retry_backoff = lock_retry_backoff
        self.init()
    
    def init(self) -> None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(ALERT_STORE_SCHEMA_SQL)
        self._conn.commit()
    
    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
    
    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._conn
    
    def _is_lock_error(self, e: Exception) -> bool:
        msg = str(e).lower()
        return "database is locked" in msg or "database is busy" in msg or "locked" in msg
    
    def _retry_on_lock(self, operation: callable) -> Any:
        last_error = None
        for attempt in range(self._lock_retry_count):
            try:
                return operation()
            except sqlite3.OperationalError as e:
                last_error = e
                if not self._is_lock_error(e):
                    raise
                if attempt < self._lock_retry_count - 1:
                    time.sleep(self._lock_retry_backoff * (attempt + 1))
        raise AlertStoreError(f"Lock retry exhausted after {self._lock_retry_count} attempts") from last_error
    
    def _row_to_alert(self, row: sqlite3.Row) -> Alert:
        return Alert(
            alert_id=row["alert_id"],
            fingerprint=row["fingerprint"],
            fingerprint_version=row["fingerprint_version"],
            server_id=row["server_id"],
            alert_type=AlertType(row["alert_type"]),
            resource_type=ResourceType(row["resource_type"]),
            resource_id=row["resource_id"],
            condition=row["condition"],
            severity=AlertSeverity(row["severity"]),
            status=AlertStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            acknowledged_at=row["acknowledged_at"],
            acknowledged_by=row["acknowledged_by"],
            acknowledge_note=row["acknowledge_note"],
            resolved_at=row["resolved_at"],
            resolution_note=row["resolution_note"],
            consecutive_failure_count=row["consecutive_failure_count"],
            consecutive_ok_count=row["consecutive_ok_count"],
            first_snapshot_id=row["first_snapshot_id"],
            last_snapshot_id=row["last_snapshot_id"],
            recovery_count=row["recovery_count"],
            metadata_json={} if row["metadata_json"] is None else json.loads(row["metadata_json"]),
        )

    def create_alert(
        self,
        server_id: str,
        alert_type: AlertType,
        resource_type: ResourceType,
        condition: str,
        severity: AlertSeverity,
        resource_id: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> Alert:
        """Create a new alert with active deduplication."""
        fingerprint = create_fingerprint(
            server_id=server_id,
            alert_type=alert_type.value,
            resource_type=resource_type.value,
            resource_id=resource_id,
            condition=condition,
            version=1,
        )
        
        # Check for existing alert with same fingerprint
        cursor = self.conn.execute(
            "SELECT alert_id, status FROM alerts WHERE fingerprint = ?",
            (fingerprint,)
        )
        existing = cursor.fetchone()
        
        if existing is not None:
            existing_status = AlertStatus(existing["status"])
            if existing_status in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED):
                raise AlertDuplicateError(f"Active alert with fingerprint {fingerprint} already exists")
            # RESOLVED - allow new alert, generate new alert_id
            now = datetime.now(timezone.utc).isoformat()
            import uuid
            alert_id = f"alert_{now}_{server_id}_{uuid.uuid4().hex[:8]}"
        else:
            now = datetime.now(timezone.utc).isoformat()
            alert_id = f"alert_{now}_{server_id}_{fingerprint[:8]}"
        
        def _create():
            cursor = self.conn.execute(
                """INSERT INTO alerts (
                    alert_id, fingerprint, fingerprint_version,
                    server_id, alert_type, resource_type, resource_id, condition,
                    severity, status, created_at, updated_at,
                    consecutive_failure_count, consecutive_ok_count,
                    first_snapshot_id, last_snapshot_id,
                    recovery_count, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    alert_id, fingerprint, 1, server_id,
                    alert_type.value, resource_type.value, resource_id, condition,
                    severity.value, AlertStatus.OPEN.value, now, now,
                    1, 0, snapshot_id, snapshot_id, 0,
                    json.dumps(metadata_json or {}),
                ),
            )
            self.conn.commit()
            return cursor.lastrowid
        
        try:
            self._retry_on_lock(_create)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise AlertDuplicateError(f"Active alert with fingerprint {fingerprint} already exists") from e
            raise
        
        return self.get_alert(alert_id)
    
    def get_alert_by_fingerprint(
        self,
        fingerprint: str,
        status_filter: Optional[list[AlertStatus]] = None,
    ) -> Optional[Alert]:
        """Get alert by fingerprint."""
        query = "SELECT * FROM alerts WHERE fingerprint = ?"
        params: list = [fingerprint]
        
        if status_filter:
            placeholders = ",".join("?" for _ in status_filter)
            query += f" AND status IN ({placeholders})"
            params.extend([s.value for s in status_filter])
        
        query += " ORDER BY created_at DESC LIMIT 1"
        
        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_alert(row)
    
    def list_alerts(
        self,
        status_filter: Optional[AlertStatus] = None,
        server_id: Optional[str] = None,
        severity_filter: Optional[AlertSeverity] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        """List alerts with optional filters."""
        query = "SELECT * FROM alerts WHERE 1=1"
        params: list = []
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter.value)
        
        if server_id:
            query += " AND server_id = ?"
            params.append(server_id)
        
        if severity_filter:
            query += " AND severity = ?"
            params.append(severity_filter.value)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = self.conn.execute(query, params)
        return [self._row_to_alert(row) for row in cursor.fetchall()]
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        acknowledge_note: Optional[str] = None,
    ) -> Alert:
        """Acknowledge an alert. Transition: OPEN → ACKNOWLEDGED."""
        alert = self.get_alert(alert_id)
        
        if alert.status != AlertStatus.OPEN:
            raise AlertInvalidTransitionError(f"Cannot acknowledge alert in {alert.status.value} status")
        
        now = datetime.now(timezone.utc).isoformat()
        
        def _update():
            cursor = self.conn.execute(
                """UPDATE alerts
                SET status = ?, acknowledged_at = ?, acknowledged_by = ?,
                    acknowledge_note = ?, updated_at = ?
                WHERE alert_id = ?""",
                (AlertStatus.ACKNOWLEDGED.value, now, acknowledged_by, acknowledge_note, now, alert_id),
            )
            self.conn.commit()
            return cursor.rowcount
        
        self._retry_on_lock(_update)
        return self.get_alert(alert_id)
    
    def resolve_alert(
        self,
        alert_id: str,
        resolution_note: Optional[str] = None,
    ) -> Alert:
        """Resolve an alert. Transition: OPEN/ACKNOWLEDGED → RESOLVED."""
        alert = self.get_alert(alert_id)
        
        if alert.status not in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED):
            raise AlertInvalidTransitionError(f"Cannot resolve alert in {alert.status.value} status")
        
        now = datetime.now(timezone.utc).isoformat()
        
        def _update():
            cursor = self.conn.execute(
                """UPDATE alerts
                SET status = ?, resolved_at = ?, resolution_note = ?, updated_at = ?
                WHERE alert_id = ?""",
                (AlertStatus.RESOLVED.value, now, resolution_note, now, alert_id),
            )
            self.conn.commit()
            return cursor.rowcount
        
        self._retry_on_lock(_update)
        return self.get_alert(alert_id)
    
    def update_counters(
        self,
        alert_id: str,
        failure: bool = True,
        snapshot_id: Optional[str] = None,
    ) -> Alert:
        """Update consecutive failure/OK counters."""
        alert = self.get_alert(alert_id)
        now = datetime.now(timezone.utc).isoformat()
        
        def _update():
            if failure:
                query = """UPDATE alerts
                SET consecutive_failure_count = consecutive_failure_count + 1,
                    consecutive_ok_count = 0, last_snapshot_id = ?, updated_at = ?
                WHERE alert_id = ?"""
                params = (snapshot_id, now, alert_id)
            else:
                query = """UPDATE alerts
                SET consecutive_ok_count = consecutive_ok_count + 1,
                    consecutive_failure_count = 0, last_snapshot_id = ?, updated_at = ?
                WHERE alert_id = ?"""
                params = (snapshot_id, now, alert_id)
            
            cursor = self.conn.execute(query, params)
            self.conn.commit()
            return cursor.rowcount
        
        self._retry_on_lock(_update)
        return self.get_alert(alert_id)
    
    def get_all_alerts(
        self,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[Alert]:
        """Get all alerts."""
        query = "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params = [limit, offset]
        
        cursor = self.conn.execute(query, params)
        return [self._row_to_alert(row) for row in cursor.fetchall()]
    
    def get_alert(self, alert_id: str) -> Alert:
        """Get alert by ID."""
        cursor = self.conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
        row = cursor.fetchone()
        
        if row is None:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        
        return self._row_to_alert(row)
