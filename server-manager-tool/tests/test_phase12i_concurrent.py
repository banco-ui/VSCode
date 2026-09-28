"""Concurrent Fingerprint Deduplication Tests — Phase 12I."""
import pytest
import threading
import uuid
from datetime import datetime, timezone

from server_manager.alert.store import AlertStore
from server_manager.alert.fingerprint import create_fingerprint
from server_manager.alert.models import AlertType, ResourceType, AlertSeverity, AlertStatus


class TestConcurrentFingerprintDedup:
    def test_concurrent_same_fingerprint_no_duplicates(self, tmp_path):
        """Verify concurrent evaluations with same fingerprint don't create duplicates."""
        db_path = tmp_path / f"test_{uuid.uuid4().hex[:8]}.db"
        store_a = AlertStore(str(db_path))
        store_b = AlertStore(str(db_path))
        
        fingerprint = create_fingerprint(
            server_id="server-001", alert_type=AlertType.HEALTH_CRITICAL.value,
            resource_type=ResourceType.SYSTEM.value, resource_id=None,
            condition="health_status=CRITICAL", version=1,
        )
        results = {'A': None, 'B': None}
        barrier = threading.Barrier(2)
        
        def create_alert(store, label):
            try:
                barrier.wait(timeout=5.0)
                store.begin_transaction()
                cursor = store.conn.execute(
                    "SELECT alert_id, status FROM alerts WHERE fingerprint = ?", (fingerprint,))
                existing = cursor.fetchone()
                if existing and AlertStatus(existing["status"]) in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED):
                    results[label] = 'DUPLICATE_PREVENTED'
                    store.rollback()
                    return
                alert_id = f"alert-{label}-{uuid.uuid4().hex[:8]}"
                now = datetime.now(timezone.utc).isoformat()
                store.conn.execute(
                    """INSERT INTO alerts (alert_id, fingerprint, fingerprint_version, server_id,
                        alert_type, resource_type, resource_id, condition, severity, status,
                        created_at, updated_at, consecutive_failure_count, consecutive_ok_count,
                        first_snapshot_id, last_snapshot_id, recovery_count, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (alert_id, fingerprint, 1, "server-001", AlertType.HEALTH_CRITICAL.value,
                     ResourceType.SYSTEM.value, None, "health_status=CRITICAL",
                     AlertSeverity.CRITICAL.value, AlertStatus.OPEN.value, now, now,
                     1, 0, f"snap-{label}", f"snap-{label}", 0, '{}'))
                store.commit()
                results[label] = 'SUCCESS'
            except Exception as e:
                results[label] = f'ERROR: {type(e).__name__}: {e}'
                store.rollback()
        
        thread_a = threading.Thread(target=create_alert, args=(store_a, 'A'))
        thread_b = threading.Thread(target=create_alert, args=(store_b, 'B'))
        thread_a.start()
        thread_b.start()
        thread_a.join(timeout=10.0)
        thread_b.join(timeout=10.0)
        
        cursor = store_a.conn.execute("SELECT alert_id, status FROM alerts WHERE fingerprint = ?", (fingerprint,))
        alerts = cursor.fetchall()
        assert len(alerts) == 1, f"Expected 1 alert, got {len(alerts)}"
        store_a.close()
        store_b.close()
    
    def test_busy_timeout_configuration(self, tmp_path):
        """Verify busy_timeout is set to 5000ms."""
        db_path = tmp_path / f"test_{uuid.uuid4().hex[:8]}.db"
        store = AlertStore(str(db_path))
        cursor = store.conn.execute("PRAGMA busy_timeout;")
        busy_timeout = cursor.fetchone()[0]
        assert busy_timeout == 5000, f"Expected busy_timeout=5000, got {busy_timeout}"
        store.close()
    
    def test_resolved_alert_allows_new_open(self, tmp_path):
        """Verify lifecycle: RESOLVED → same fingerprint → NEW OPEN."""
        db_path = tmp_path / f"test_{uuid.uuid4().hex[:8]}.db"
        store = AlertStore(str(db_path))
        fingerprint = create_fingerprint(server_id="server-001", alert_type=AlertType.HEALTH_CRITICAL.value,
            resource_type=ResourceType.SYSTEM.value, resource_id=None, condition="health_status=CRITICAL", version=1)
        alert1 = store.create_alert(server_id="server-001", alert_type=AlertType.HEALTH_CRITICAL,
            resource_type=ResourceType.SYSTEM, condition="health_status=CRITICAL",
            severity=AlertSeverity.CRITICAL, snapshot_id="snap-001")
        assert alert1.status == AlertStatus.OPEN
        store.resolve_alert(alert1.alert_id, resolution_note="Test")
        alert1_resolved = store.get_alert(alert1.alert_id)
        assert alert1_resolved.status == AlertStatus.RESOLVED
        alert2 = store.create_alert(server_id="server-001", alert_type=AlertType.HEALTH_CRITICAL,
            resource_type=ResourceType.SYSTEM, condition="health_status=CRITICAL",
            severity=AlertSeverity.CRITICAL, snapshot_id="snap-002")
        assert alert2.status == AlertStatus.OPEN
        assert alert2.fingerprint == fingerprint
        store.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
