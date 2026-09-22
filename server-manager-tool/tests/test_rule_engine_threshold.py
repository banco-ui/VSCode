"""Tests for Alert Rule Engine N=3 / M=5 Thresholds — Phase 11D-1-Fix."""
import pytest
from src.server_manager.alert import (
    AlertStore,
    RuleEngine,
    AlertEvaluationContext,
    AlertStatus,
    AlertType,
    FAILURE_THRESHOLD,
    RECOVERY_THRESHOLD,
)


class TestN3Threshold:
    """Test N=3 failure threshold."""
    
    @pytest.fixture
    def store(self):
        return AlertStore(":memory:")
    
    @pytest.fixture
    def engine(self, store):
        return RuleEngine(store)
    
    def test_one_failure_no_alert(self, engine):
        """1 failure should not create alert."""
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=False,
        )
        result = engine.evaluate(ctx)
        
        assert result.alerts_created == 0
        assert result.alerts_updated == 0
    
    def test_two_failures_no_alert(self, engine):
        """2 consecutive failures should not create alert."""
        # First failure
        ctx1 = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=False,
        )
        engine.evaluate(ctx1)
        
        # Second failure
        ctx2 = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap002",
            collection_success=False,
        )
        result2 = engine.evaluate(ctx2)
        
        assert result2.alerts_created == 0
        assert result2.alerts_updated == 0
    
    def test_three_failures_creates_alert(self, engine):
        """3 consecutive failures should create alert."""
        # First two failures
        for i in range(2):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+1}",
                collection_success=False,
            )
            engine.evaluate(ctx)
        
        # Third failure
        ctx3 = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap003",
            collection_success=False,
        )
        result3 = engine.evaluate(ctx3)
        
        assert result3.alerts_created == 1
    
    def test_failure_reset_on_ok(self, engine):
        """OK observation should reset failure counter."""
        # Two failures
        for i in range(2):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+1}",
                collection_success=False,
            )
            engine.evaluate(ctx)
        
        # OK observation
        ctx_ok = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap003",
            collection_success=True,
            health_status="OK",
        )
        engine.evaluate(ctx_ok)
        
        # Next failure should be count 1
        ctx_fail = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap004",
            collection_success=False,
        )
        result = engine.evaluate(ctx_fail)
        
        # Should not create alert (count=1)
        assert result.alerts_created == 0
    
    def test_different_condition_separate_counter(self, engine):
        """Different conditions should have separate counters."""
        # Two collection failures
        for i in range(2):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+1}",
                collection_success=False,
            )
            engine.evaluate(ctx)
        
        # One health critical (different condition)
        ctx_health = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap003",
            health_status="CRITICAL",
        )
        result = engine.evaluate(ctx_health)
        
        # Should not create alert (health critical count=1)
        assert result.alerts_created == 0


class TestM5Recovery:
    """Test M=5 recovery threshold."""
    
    @pytest.fixture
    def store(self):
        return AlertStore(":memory:")
    
    @pytest.fixture
    def engine_with_alert(self, store):
        """Create engine with an existing alert."""
        engine = RuleEngine(store)
        
        # Create alert with 3 failures
        for i in range(3):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+1}",
                collection_success=False,
            )
            engine.evaluate(ctx)
        
        return engine
    
    def test_four_ok_no_resolution(self, engine_with_alert):
        """4 OKs should not resolve alert."""
        # 4 OK observations
        for i in range(4):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+4}",
                collection_success=True,
                health_status="OK",
            )
            result = engine_with_alert.evaluate(ctx)
        
        # Alert should still be OPEN
        alerts = engine_with_alert.alert_store.list_alerts(
            server_id="srv01",
            status_filter=AlertStatus.OPEN,
        )
        assert len(alerts) == 1
    
    def test_five_ok_resolves_alert(self, engine_with_alert):
        """5 consecutive OKs should resolve alert."""
        # 5 OK observations
        for i in range(5):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+4}",
                collection_success=True,
                health_status="OK",
            )
            result = engine_with_alert.evaluate(ctx)
        
        # Alert should be RESOLVED
        resolved = engine_with_alert.alert_store.list_alerts(
            server_id="srv01",
            status_filter=AlertStatus.RESOLVED,
        )
        assert len(resolved) == 1
        
        open_alerts = engine_with_alert.alert_store.list_alerts(
            server_id="srv01",
            status_filter=AlertStatus.OPEN,
        )
        assert len(open_alerts) == 0
    
    def test_ok_reset_on_failure(self, engine_with_alert):
        """Failure should reset OK counter."""
        # 2 OKs
        for i in range(2):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+4}",
                collection_success=True,
            )
            engine_with_alert.evaluate(ctx)
        
        # Failure
        ctx_fail = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap006",
            collection_success=False,
        )
        engine_with_alert.evaluate(ctx_fail)
        
        # 4 more OKs
        for i in range(4):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+7}",
                collection_success=True,
            )
            result = engine_with_alert.evaluate(ctx)
        
        # Should not resolve (OK count reset, now at 4)
        open_alerts = engine_with_alert.alert_store.list_alerts(
            server_id="srv01",
            status_filter=AlertStatus.OPEN,
        )
        assert len(open_alerts) == 1
    
    def test_acknowledged_ok_count(self, engine_with_alert):
        """ACKNOWLEDGED alert should also count OKs."""
        # Acknowledge the alert
        alerts = engine_with_alert.alert_store.list_alerts(
            server_id="srv01",
            status_filter=AlertStatus.OPEN,
        )
        engine_with_alert.alert_store.acknowledge_alert(
            alerts[0].alert_id,
            acknowledged_by="test",
        )
        
        # 5 OK observations
        for i in range(5):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+4}",
                collection_success=True,
            )
            engine_with_alert.evaluate(ctx)
        
        # Should be RESOLVED
        resolved = engine_with_alert.alert_store.list_alerts(
            server_id="srv01",
            status_filter=AlertStatus.RESOLVED,
        )
        assert len(resolved) == 1


class TestReappearance:
    """Test RESOLVED alert reappearance."""
    
    @pytest.fixture
    def store(self):
        return AlertStore(":memory:")
    
    @pytest.fixture
    def engine_resolved(self, store):
        """Create engine with resolved alert."""
        engine = RuleEngine(store)
        
        # Create and resolve alert
        for i in range(3):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+1}",
                collection_success=False,
            )
            engine.evaluate(ctx)
        
        # 5 OKs to resolve
        for i in range(5):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+4}",
                collection_success=True,
            )
            engine.evaluate(ctx)
        
        return engine
    
    def test_resolved_two_failures_no_new_alert(self, engine_resolved):
        """RESOLVED + 2 failures should not create new alert."""
        for i in range(2):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+10}",
                collection_success=False,
            )
            result = engine_resolved.evaluate(ctx)
        
        assert result.alerts_created == 0
    
    def test_resolved_three_failures_new_alert(self, engine_resolved):
        """RESOLVED + 3 failures should create new alert."""
        for i in range(3):
            ctx = AlertEvaluationContext(
                server_id="srv01",
                snapshot_id=f"snap00{i+10}",
                collection_success=False,
            )
            result = engine_resolved.evaluate(ctx)
        
        assert result.alerts_created == 1


class TestIdempotencyThreshold:
    """Test snapshot_id idempotency with thresholds."""
    
    @pytest.fixture
    def store(self):
        return AlertStore(":memory:")
    
    @pytest.fixture
    def engine(self, store):
        return RuleEngine(store)
    
    def test_same_snapshot_failure_once(self, engine):
        """Same snapshot failure should only count once."""
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=False,
        )
        
        result1 = engine.evaluate(ctx)
        result2 = engine.evaluate(ctx)
        
        assert result1.alerts_created == 0
        assert result2.evaluated is False
        assert result2.duplicates_ignored == 1