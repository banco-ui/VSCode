import sys
sys.path.insert(0, 'src')

from server_manager.alert.engine import AlertEngine, AlertEngineResult
from server_manager.alert.rule_engine import AlertEvaluationContext
from server_manager.alert.store import AlertStore

print("=" * 60)
print("PHASE 12B - TRANSACTION BOUNDARY VERIFICATION")
print("=" * 60)

# Create AlertStore and AlertEngine
store = AlertStore(db_path=":memory:")
store.init()
engine = AlertEngine(store)

print("\n=== Test 1: Single Evaluation - All Operations Atomic ===")
ctx = AlertEvaluationContext(
    server_id="srv01",
    snapshot_id="snap001",
    collection_success=False,  # Force failure path
    health_status="CRITICAL",
)

print(f"Before evaluate: _in_transaction={store._in_transaction}")
result = engine.evaluate(ctx)
print(f"After evaluate: _in_transaction={store._in_transaction}")
print(f"Evaluation result: success={result.success}")

# Check what happened
alerts = store.list_alerts()
print(f"Alerts in store: {len(alerts)}")
eval_logs = store.conn.execute("SELECT * FROM evaluation_log").fetchall()
print(f"Evaluation logs: {len(eval_logs)}")

print("\n=== Test 2: Duplicate Snapshot Evaluation ===")
ctx2 = AlertEvaluationContext(
    server_id="srv01",
    snapshot_id="snap001",
    collection_success=False,
)
result2 = engine.evaluate(ctx2)
print(f"Result: evaluated={result2.evaluation_result.evaluated if result2.evaluation_result else 'N/A'}")

print("\n=== Test 3: Verify Transaction Flow ===")
# Manual transaction test
print("Manual transaction test:")
store.begin_transaction()
print(f"  After begin: _in_transaction={store._in_transaction}")
store.commit()
print(f"  After commit: _in_transaction={store._in_transaction}")

print("\n" + "=" * 60)
print("PHASE 12B VERIFICATION COMPLETE")
print("=" * 60)
