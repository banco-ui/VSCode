"""AlertStore Tests - Phase 11C."""
from __future__ import annotations

import pytest

from src.server_manager.alert.store import (
    AlertStore, AlertNotFoundError, AlertDuplicateError, AlertInvalidTransitionError,
)
from src.server_manager.alert.models import (
    AlertStatus, AlertSeverity, AlertType, ResourceType,
)
from src.server_manager.alert.fingerprint import create_fingerprint, validate_fingerprint


class TestFingerprint:
    def test_deterministic_fingerprint(self):
        fp1 = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        fp2 = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        assert fp1 == fp2

    def test_fingerprint_length(self):
        fp = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        assert len(fp) == 64

    def test_fingerprint_valid_hex(self):
        fp = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        assert validate_fingerprint(fp) is True

    def test_different_server_different_fingerprint(self):
        fp1 = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        fp2 = create_fingerprint("srv02", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        assert fp1 != fp2

    def test_different_resource_different_fingerprint(self):
        fp1 = create_fingerprint("srv01", "HEALTH_CRITICAL", "physical_disk", "disk-01", "health == CRITICAL")
        fp2 = create_fingerprint("srv01", "HEALTH_CRITICAL", "physical_disk", "disk-02", "health == CRITICAL")
        assert fp1 != fp2

    def test_different_condition_different_fingerprint(self):
        fp1 = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        fp2 = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == WARNING")
        assert fp1 != fp2

    def test_resource_id_none_normalization(self):
        fp1 = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", None, "health == CRITICAL")
        fp2 = create_fingerprint("srv01", "HEALTH_CRITICAL", "system", "", "health == CRITICAL")
        assert fp1 == fp2


class TestAlertStoreSchema:
    def test_initialization(self):
        store = AlertStore(db_path=":memory:")
        assert store.conn is not None
        store.close()

    def test_alerts_table_exists(self):
        store = AlertStore(db_path=":memory:")
        cursor = store.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
        row = cursor.fetchone()
        assert row is not None
        assert row["name"] == "alerts"
        store.close()

    def test_expected_columns(self):
        store = AlertStore(db_path=":memory:")
        cursor = store.conn.execute("PRAGMA table_info(alerts)")
        columns = {row["name"] for row in cursor.fetchall()}
        expected = {"alert_id", "fingerprint", "fingerprint_version", "server_id", "alert_type",
                    "resource_type", "resource_id", "condition", "severity", "status",
                    "created_at", "updated_at", "acknowledged_at", "acknowledged_by",
                    "acknowledge_note", "resolved_at", "resolution_note",
                    "consecutive_failure_count", "consecutive_ok_count",
                    "first_snapshot_id", "last_snapshot_id", "recovery_count", "metadata_json"}
        assert expected.issubset(columns)
        store.close()

    def test_indexes_exist(self):
        store = AlertStore(db_path=":memory:")
        cursor = store.conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='alerts'")
        indexes = {row["name"] for row in cursor.fetchall()}
        expected = {"idx_alerts_fingerprint", "idx_alerts_status", "idx_alerts_server_id",
                    "idx_alerts_severity", "idx_alerts_status_server", "idx_alerts_created_at"}
        assert expected.issubset(indexes)
        store.close()

    def test_application_level_deduplication(self):
        store = AlertStore(db_path=":memory:")
        alert1 = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                   resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                   severity=AlertSeverity.CRITICAL)
        with pytest.raises(AlertDuplicateError):
            store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                              resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                              severity=AlertSeverity.CRITICAL)
        store.close()


class TestAlertStoreCRUD:
    @pytest.fixture
    def store(self):
        store = AlertStore(db_path=":memory:")
        yield store
        store.close()

    def test_create_alert(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                   resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                   severity=AlertSeverity.CRITICAL)
        assert alert.alert_id.startswith("alert_")
        assert alert.server_id == "srv01"
        assert alert.status == AlertStatus.OPEN
        assert alert.consecutive_failure_count == 1

    def test_get_alert(self, store):
        created = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                     resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                     severity=AlertSeverity.CRITICAL)
        retrieved = store.get_alert(created.alert_id)
        assert retrieved.alert_id == created.alert_id

    def test_get_alert_not_found(self, store):
        with pytest.raises(AlertNotFoundError):
            store.get_alert("nonexistent")

    def test_list_alerts(self, store):
        store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                          resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                          severity=AlertSeverity.CRITICAL)
        store.create_alert(server_id="srv02", alert_type=AlertType.HEALTH_WARNING,
                          resource_type=ResourceType.SYSTEM, condition="health == WARNING",
                          severity=AlertSeverity.WARNING)
        all_alerts = store.list_alerts()
        assert len(all_alerts) == 2
        srv01_alerts = store.list_alerts(server_id="srv01")
        assert len(srv01_alerts) == 1

    def test_get_all_alerts(self, store):
        for i in range(5):
            store.create_alert(server_id=f"srv{i:02d}", alert_type=AlertType.HEALTH_CRITICAL,
                              resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                              severity=AlertSeverity.CRITICAL)
        all_alerts = store.get_all_alerts(limit=10)
        assert len(all_alerts) == 5


class TestAlertLifecycle:
    @pytest.fixture
    def store(self):
        store = AlertStore(db_path=":memory:")
        yield store
        store.close()

    def test_open_to_acknowledged(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                   resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                   severity=AlertSeverity.CRITICAL)
        ack = store.acknowledge_alert(alert.alert_id, acknowledged_by="admin", acknowledge_note="Investigating")
        assert ack.status == AlertStatus.ACKNOWLEDGED
        assert ack.acknowledged_by == "admin"

    def test_open_to_resolved(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                   resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                   severity=AlertSeverity.CRITICAL)
        resolved = store.resolve_alert(alert.alert_id, resolution_note="Condition cleared")
        assert resolved.status == AlertStatus.RESOLVED
        assert resolved.resolution_note == "Condition cleared"

    def test_acknowledged_to_resolved(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                   resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                   severity=AlertSeverity.CRITICAL)
        store.acknowledge_alert(alert.alert_id, acknowledged_by="admin")
        resolved = store.resolve_alert(alert.alert_id)
        assert resolved.status == AlertStatus.RESOLVED

    def test_invalid_transition_resolved_to_acknowledged(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                   resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                   severity=AlertSeverity.CRITICAL)
        store.resolve_alert(alert.alert_id)
        with pytest.raises(AlertInvalidTransitionError):
            store.acknowledge_alert(alert.alert_id, acknowledged_by="admin")

    def test_invalid_transition_acknowledge_already_acknowledged(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                   resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                   severity=AlertSeverity.CRITICAL)
        store.acknowledge_alert(alert.alert_id, acknowledged_by="admin")
        with pytest.raises(AlertInvalidTransitionError):
            store.acknowledge_alert(alert.alert_id, acknowledged_by="admin2")


class TestActiveDeduplication:
    @pytest.fixture
    def store(self):
        store = AlertStore(db_path=":memory:")
        yield store
        store.close()

    def test_duplicate_open_rejected(self, store):
        store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                          resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                          severity=AlertSeverity.CRITICAL)
        with pytest.raises(AlertDuplicateError):
            store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                              resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                              severity=AlertSeverity.CRITICAL)

    def test_duplicate_acknowledged_rejected(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                  resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                  severity=AlertSeverity.CRITICAL)
        store.acknowledge_alert(alert.alert_id, acknowledged_by="admin")
        with pytest.raises(AlertDuplicateError):
            store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                              resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                              severity=AlertSeverity.CRITICAL)

    def test_resolved_allows_new_alert(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                  resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                  severity=AlertSeverity.CRITICAL)
        store.resolve_alert(alert.alert_id)
        new_alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                      resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                      severity=AlertSeverity.CRITICAL)
        assert new_alert.alert_id != alert.alert_id
        assert new_alert.fingerprint == alert.fingerprint
        assert new_alert.status == AlertStatus.OPEN


class TestCounterPersistence:
    @pytest.fixture
    def store(self):
        store = AlertStore(db_path=":memory:")
        yield store
        store.close()

    def test_failure_counter_increments(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                  resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                  severity=AlertSeverity.CRITICAL)
        assert alert.consecutive_failure_count == 1
        alert2 = store.update_counters(alert.alert_id, failure=True)
        assert alert2.consecutive_failure_count == 2
        alert3 = store.update_counters(alert2.alert_id, failure=True)
        assert alert3.consecutive_failure_count == 3

    def test_ok_counter_resets_failure(self, store):
        alert = store.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                  resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                  severity=AlertSeverity.CRITICAL)
        store.update_counters(alert.alert_id, failure=True)
        store.update_counters(alert.alert_id, failure=True)
        alert_ok = store.update_counters(alert.alert_id, failure=False)
        assert alert_ok.consecutive_failure_count == 0
        assert alert_ok.consecutive_ok_count == 1


class TestSnapshotReferences:
    @pytest.fixture
    def store(self):
        store = AlertStore(db_path=":memory:")
        yield store
        store.close()

    def test_snapshot_ids_persisted(self, store):
        snapshot_id = "snap_20260921_001"


class TestPersistence:
    def test_alert_survives_restart(self, tmp_path):
        db_file = tmp_path / "alerts.db"
        store1 = AlertStore(db_path=str(db_file))
        alert1 = store1.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                    resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                    severity=AlertSeverity.CRITICAL)
        store1.close()
        store2 = AlertStore(db_path=str(db_file))
        alert2 = store2.get_alert(alert1.alert_id)
        assert alert2.alert_id == alert1.alert_id
        store2.close()

    def test_counters_survive_restart(self, tmp_path):
        db_file = tmp_path / "alerts.db"
        store1 = AlertStore(db_path=str(db_file))
        alert1 = store1.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                    resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                    severity=AlertSeverity.CRITICAL)
        store1.update_counters(alert1.alert_id, failure=True)
        store1.update_counters(alert1.alert_id, failure=True)
        store1.close()
        store2 = AlertStore(db_path=str(db_file))
        alert2 = store2.get_alert(alert1.alert_id)
        assert alert2.consecutive_failure_count == 3
        store2.close()

    def test_acknowledgement_survives_restart(self, tmp_path):
        db_file = tmp_path / "alerts.db"
        store1 = AlertStore(db_path=str(db_file))
        alert1 = store1.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                    resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                    severity=AlertSeverity.CRITICAL)
        store1.acknowledge_alert(alert1.alert_id, acknowledged_by="admin", acknowledge_note="Test note")
        store1.close()
        store2 = AlertStore(db_path=str(db_file))
        alert2 = store2.get_alert(alert1.alert_id)
        assert alert2.status == AlertStatus.ACKNOWLEDGED
        assert alert2.acknowledged_by == "admin"
        store2.close()

    def test_resolution_survives_restart(self, tmp_path):
        db_file = tmp_path / "alerts.db"
        store1 = AlertStore(db_path=str(db_file))
        alert1 = store1.create_alert(server_id="srv01", alert_type=AlertType.HEALTH_CRITICAL,
                                    resource_type=ResourceType.SYSTEM, condition="health == CRITICAL",
                                    severity=AlertSeverity.CRITICAL)
        store1.resolve_alert(alert1.alert_id, resolution_note="Fixed")
        store1.close()
        store2 = AlertStore(db_path=str(db_file))
        alert2 = store2.get_alert(alert1.alert_id)
        assert alert2.status == AlertStatus.RESOLVED
        assert alert2.resolution_note == "Fixed"
        store2.close()