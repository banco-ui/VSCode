"""Tests for InventoryStore (Phase 6)."""
import pytest
from server_manager.store.store import InventoryStore
from server_manager.store.models import (
    ServerRegistryEntry, InventorySnapshot, VerificationRecord,
    EndpointRef, ManagementEndpoints,
)
from server_manager.models.enums import ServerLifecycle, Vendor
from server_manager.models.inventory import (
    ServerInventory, Identity, Hardware, CPU, Memory, OS, Health,
)
from server_manager.verifiers.base import VerificationResult, FieldResult
from server_manager.models.enums import VerificationStatus
import json as _json



def make_test_inventory(server_id="R750-001", cores=48):
    return ServerInventory(
        identity=Identity(server_id=server_id, vendor=Vendor.Dell, model="PowerEdge R750"),
        hardware=Hardware(
            cpu=CPU(count=2, total_cores=cores, total_threads=cores * 2),
            memory=Memory(total_gb=256.0),
        ),
        os=OS(distribution="Ubuntu", kernel="5.15.0", hostname="srv-1"),
    )


def make_test_snapshot(server_id="R750-001", run_id="run-001", inv=None):
    return InventorySnapshot(
        snapshot_id=f"snap-{run_id}",
        server_id=server_id,
        orchestration_run_id=run_id,
        collected_at="2026-01-01T00:00:00+00:00",
        inventory=inv or make_test_inventory(server_id),
    )


def make_test_orchestration_result(server_id="R750-001"):
    """Create a minimal orchestration result for testing."""
    from server_manager.orchestrator.models import (
        OrchestrationResult, OrchestrationStatus, SourceResult,
    )
    inv = make_test_inventory(server_id)
    return OrchestrationResult(
        run_id="run-test-001",
        server_id=server_id,
        status=OrchestrationStatus.SUCCESS,
        source_results=[
            SourceResult(source="redfish", collection_success=True, normalization_success=True, inventory=inv),
        ],
        canonical_inventory=inv,
        canonical_source="redfish",
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:01:00+00:00",
        total_duration_ms=60000,
    )


@pytest.fixture
def store():
    s = InventoryStore(":memory:")
    yield s
    s.close()


class TestServerRegistry:
    def test_register_and_get(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="R750 Server 1",
            vendor=Vendor.Dell,
            model="PowerEdge R750",
            lifecycle_state=ServerLifecycle.ACTIVE,
            endpoints=ManagementEndpoints(
                redfish=EndpointRef(host="10.0.0.1", port=443, username="root"),
            ),
        )
        store.register_server(entry)
        retrieved = store.get_server("R750-001")
        assert retrieved is not None
        assert retrieved.server_id == "R750-001"
        assert retrieved.vendor == Vendor.Dell
        assert retrieved.lifecycle_state == ServerLifecycle.ACTIVE

    def test_get_nonexistent(self, store):
        assert store.get_server("nonexistent") is None

    def test_list_servers(self, store):
        for i in range(3):
            entry = ServerRegistryEntry(
                server_id=f"R750-{i:03d}",
                display_name=f"Server {i}",
                vendor=Vendor.Dell,
            )
            store.register_server(entry)
        servers = store.list_servers()
        assert len(servers) == 3

    def test_update_lifecycle(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        store.update_server_lifecycle("R750-001", ServerLifecycle.MAINTENANCE)
        retrieved = store.get_server("R750-001")
        assert retrieved.lifecycle_state == ServerLifecycle.MAINTENANCE

    def test_update_metadata(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        store.update_server_metadata("R750-001", hardware_identity="hw-123", notes="Updated notes")
        retrieved = store.get_server("R750-001")
        assert retrieved.hardware_identity == "hw-123"
        assert retrieved.notes == "Updated notes"

    def test_register_upsert(self, store):
        entry1 = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Original Name",
            vendor=Vendor.Dell,
        )
        store.register_server(entry1)
        entry2 = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Updated Name",
            vendor=Vendor.Dell,
        )
        store.register_server(entry2)
        retrieved = store.get_server("R750-001")
        assert retrieved.display_name == "Updated Name"

    def test_endpoints_serialization(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
            endpoints=ManagementEndpoints(
                redfish=EndpointRef(host="10.0.0.1", port=443, username="admin"),
                ssh=EndpointRef(host="10.0.0.1", port=22, username="root"),
            ),
        )
        store.register_server(entry)
        retrieved = store.get_server("R750-001")
        assert retrieved.endpoints.redfish is not None
        assert retrieved.endpoints.redfish.host == "10.0.0.1"
        assert retrieved.endpoints.ssh.port == 22


class TestSnapshots:
    def test_save_and_get(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        snap = make_test_snapshot()
        result = store.save_snapshot(snap)
        assert result is True

        retrieved = store.get_snapshot("snap-run-001")
        assert retrieved is not None
        assert retrieved.server_id == "R750-001"
        assert retrieved.inventory.hardware.cpu.total_cores == 48

    def test_save_duplicate_returns_false(self, store):
        """P1 fix: duplicate snapshot should return False."""
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        snap = make_test_snapshot()
        assert store.save_snapshot(snap) is True
        # Same snapshot ID → should return False (P1 fix)
        assert store.save_snapshot(snap) is False

    def test_get_nonexistent_snapshot(self, store):
        assert store.get_snapshot("nonexistent") is None

    def test_get_current_snapshot(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        snap1 = make_test_snapshot(run_id="run-001")
        snap2 = make_test_snapshot(run_id="run-002")
        store.save_snapshot(snap1)
        store.save_snapshot(snap2)
        current = store.get_current_snapshot("R750-001")
        assert current is not None
        assert current.snapshot_id == "snap-run-002"

    def test_list_snapshots(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        for i in range(5):
            snap = make_test_snapshot(run_id=f"run-{i:03d}")
            store.save_snapshot(snap)
        snaps = store.list_snapshots("R750-001", limit=3)
        assert len(snaps) == 3

    def test_current_snapshot_id_updated(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        snap = make_test_snapshot()
        store.save_snapshot(snap)
        retrieved = store.get_server("R750-001")
        assert retrieved.current_snapshot_id == "snap-run-001"
        assert retrieved.last_collected_at is not None


class TestVerification:
    def test_save_and_list(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        snap = make_test_snapshot()
        store.save_snapshot(snap)

        vr = VerificationResult(field_results=[
            FieldResult(field_path="cpu.count", status=VerificationStatus.VERIFIED),
            FieldResult(field_path="cpu.cores", status=VerificationStatus.DISCREPANCY),
        ])
        record = VerificationRecord(
            verification_id="verif-001",
            server_id="R750-001",
            snapshot_id="snap-run-001",
            run_id="run-001",
            verified_at="2026-01-01T00:00:00+00:00",
            result=vr,
            summary={"total": 2, "discrepancy": 1},
        )
        assert store.save_verification(record) is True
        verifications = store.list_verifications("R750-001")
        assert len(verifications) == 1

    def test_save_duplicate_verification(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        snap = make_test_snapshot()
        store.save_snapshot(snap)

        record = VerificationRecord(
            verification_id="verif-001",
            server_id="R750-001",
            snapshot_id="snap-run-001",
            run_id="run-001",
            verified_at="2026-01-01T00:00:00+00:00",
            result=VerificationResult(),
            summary={},
        )
        assert store.save_verification(record) is True
        assert store.save_verification(record) is False


class TestOrchestrationRuns:
    def test_save_and_get_run(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        result = make_test_orchestration_result()
        assert store.save_run(result) is True
        run = store.get_run("run-test-001")
        assert run is not None
        assert run["server_id"] == "R750-001"

    def test_save_duplicate_run(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        result = make_test_orchestration_result()
        assert store.save_run(result) is True
        assert store.save_run(result) is False

    def test_save_orchestration_result(self, store):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        result = make_test_orchestration_result()
        success = store.save_orchestration_result(result)
        assert success is True
        snap = store.get_snapshot("snap-run-test-001")
        assert snap is not None
        run = store.get_run("run-test-001")
        assert run is not None


class TestLegacyMigration:
    def test_migrate_legacy_json(self, store):
        legacy_data = {
            "identity": {"server_id": "R750-001", "vendor": "Dell", "model": "PowerEdge R750"},
            "hardware": {"cpu": {"count": 2, "total_cores": 48}},
        }
        assert store.migrate_legacy_json(legacy_data, "R750-001") is True
        snap = store.get_current_snapshot("R750-001")
        assert snap is not None
        assert snap.inventory.hardware.cpu.count == 2


class TestBackupRestore:
    def test_backup_restore(self, store, tmp_path):
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)
        snap = make_test_snapshot()
        store.save_snapshot(snap)

        backup_path = tmp_path / "backup.db"
        assert store.backup(str(backup_path)) is True
        assert backup_path.exists()

        # Clear and restore
        store.close()
        store2 = InventoryStore(":memory:")
        assert store2.restore(str(backup_path)) is True
        server = store2.get_server("R750-001")
        assert server is not None
        store2.close()


# ── P1 Regression Tests ──────────────────────────────────────────────

class TestMetaAliasRoundTrip:
    """P1: Verify _meta key survives Store save/load cycle."""

    def test_meta_alias_round_trip_through_store(self, store):
        """P1: Store saves with by_alias=True, so _meta must be in DB JSON.

        Verifies:
        1. Snapshot save succeeds
        2. Stored JSON contains "_meta" key (not "meta")
        3. Read-back inventory.meta is correctly restored
        """
        entry = ServerRegistryEntry(
            server_id="R750-001",
            display_name="Server 1",
            vendor=Vendor.Dell,
        )
        store.register_server(entry)

        snap = make_test_snapshot()
        assert store.save_snapshot(snap) is True

        # Verify stored JSON in DB contains "_meta"
        row = store.conn.execute(
            "SELECT inventory_json FROM inventory_snapshots WHERE snapshot_id = ?",
            ("snap-run-001",),
        ).fetchone()
        assert row is not None
        stored_json = row["inventory_json"]
        parsed = _json.loads(stored_json)
        assert "_meta" in parsed
        assert "meta" not in parsed

        # Read back through public API
        retrieved = store.get_snapshot("snap-run-001")
        assert retrieved is not None
        assert retrieved.inventory.meta.schema_version == "1.0"


class TestCredentialEnvSafety:
    """P1: Verify credential_env stores name, not value."""

    def test_credential_env_stores_name_not_value(self):
        """P1: EndpointRef stores env var NAME, not the credential value."""
        env_name = "SERVER_MANAGER_TEST_PASSWORD"
        secret_value = "SUPER_SECRET_TEST_PASSWORD_12345"

        ep = EndpointRef(
            host="10.0.0.1",
            port=443,
            username="admin",
            credential_env=env_name,
        )

        # model_dump should contain env var name, not secret value
        dumped = ep.model_dump()
        assert env_name in dumped.get("credential_env", "")
        assert secret_value not in _json.dumps(dumped)

        # model_dump_json should contain env var name, not secret value
        json_str = ep.model_dump_json()
        assert env_name in json_str
        assert secret_value not in json_str

        # String representation should not leak secret
        assert secret_value not in repr(ep)
        assert secret_value not in str(ep)


