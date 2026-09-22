"""Tests for Alert Rule Engine — Phase 11D-1."""
import pytest
from src.server_manager.alert import (
    AlertStore,
    RuleEngine,
    AlertEvaluationContext,
    AlertStatus,
    FAILURE_THRESHOLD,
    RECOVERY_THRESHOLD,
)


class TestAlertEvaluationContext:
    """Test AlertEvaluationContext."""
    
    def test_context_creation(self):
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
        )
        assert ctx.server_id == "srv01"
        assert ctx.snapshot_id == "snap001"
        assert ctx.collection_success is True
    
    def test_context_with_failure(self):
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=False,
        )
        assert ctx.collection_success is False


class TestRuleEngineBasic:
    """Test basic RuleEngine functionality."""
    
    @pytest.fixture
    def store(self):
        return AlertStore(":memory:")
    
    @pytest.fixture
    def engine(self, store):
        return RuleEngine(store)
    
    def test_evaluate_success_no_alert(self, engine):
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=True,
            health_status="OK",
        )
        result = engine.evaluate(ctx)
        assert result.evaluated is True
        assert result.alerts_created == 0
    
    def test_evaluate_collection_failure_creates_alert(self, engine):
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=False,
        )
        result = engine.evaluate(ctx)
        assert result.alerts_created == 1
    
    def test_evaluate_health_critical_creates_alert(self, engine):
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            health_status="CRITICAL",
        )
        result = engine.evaluate(ctx)
        assert result.alerts_created == 1


class TestIdempotency:
    """Test evaluation idempotency."""
    
    @pytest.fixture
    def store(self):
        return AlertStore(":memory:")
    
    @pytest.fixture
    def engine(self, store):
        return RuleEngine(store)
    
    def test_same_snapshot_not_evaluated_twice(self, engine):
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=False,
        )
        
        result1 = engine.evaluate(ctx)
        assert result1.evaluated is True
        assert result1.alerts_created == 1
        
        result2 = engine.evaluate(ctx)
        assert result2.evaluated is False
        assert result2.duplicates_ignored == 1
        assert result2.alerts_created == 0
    
    def test_different_snapshot_evaluated(self, engine):
        """Test different snapshots are evaluated (same condition updates alert)."""
        ctx1 = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap001",
            collection_success=False,
        )
        ctx2 = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="snap002",
            collection_success=False,
        )
        
        result1 = engine.evaluate(ctx1)
        result2 = engine.evaluate(ctx2)
        
        assert result1.evaluated is True
        assert result2.evaluated is True
        assert result1.alerts_created == 1
        # Same condition updates existing alert, doesn't create new one
        assert result2.alerts_updated == 1


class TestContextValidation:
    """Test context validation."""
    
    @pytest.fixture
    def store(self):
        return AlertStore(":memory:")
    
    @pytest.fixture
    def engine(self, store):
        return RuleEngine(store)
    
    def test_missing_server_id(self, engine):
        ctx = AlertEvaluationContext(
            server_id="",
            snapshot_id="snap001",
        )
        with pytest.raises(ValueError, match="server_id is required"):
            engine.evaluate(ctx)
    
    def test_missing_snapshot_id(self, engine):
        ctx = AlertEvaluationContext(
            server_id="srv01",
            snapshot_id="",
        )
        with pytest.raises(ValueError, match="snapshot_id is required"):
            engine.evaluate(ctx)