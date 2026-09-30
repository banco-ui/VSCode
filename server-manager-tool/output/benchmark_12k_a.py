"""PHASE 12K-A - SINGLE-CONNECTION PERFORMANCE BENCHMARK"""
import json, os, sqlite3, sys, tempfile, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from server_manager.alert.store import AlertStore
from server_manager.alert.models import AlertSeverity, AlertType, ResourceType

WARMUP, MEASUREMENT, ROUNDS = 20, 100, 3

def pctl(d, p):
    if not d: return 0.0
    s = sorted(d); n = len(s); k = (n-1)*p/100; f = int(k); c = min(f+1, n-1)
    return s[f]*(c-k) + s[c]*(k-f) if f != c else s[f]

def stats(s):
    if not s: return {"min":0,"max":0,"mean":0,"std":0,"p50":0,"p95":0,"p99":0}
    return {"min":min(s),"max":max(s),"mean":mean(s),"std":stdev(s) if len(s)>1 else 0,
            "p50":pctl(s,50),"p95":pctl(s,95),"p99":pctl(s,99)}

class Result:
    def __init__(self, name):
        self.name, self.samples, self.ok, self.err, self.elapsed = name, [], 0, 0, 0.0
    def record(self, lat, ok):
        self.samples.append(lat); self.elapsed += lat
        if ok: self.ok += 1

def bench_tx(store, n):
    r = Result("Transaction")
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            store.begin_transaction(); store.conn.execute("SELECT 1"); store.commit()
            r.record((time.perf_counter()-t0)*1000, True)
        except Exception:
            r.record((time.perf_counter()-t0)*1000, False)
    return r

def bench_create(store, n):
    r = Result("Alert Create")
    for i in range(n):
        t0 = time.perf_counter()
        try:
            store.begin_transaction()
            store.create_alert(server_id="srv", alert_type=AlertType.HEALTH_CRITICAL,
                resource_type=ResourceType.SYSTEM, resource_id=f"r-{i}", condition="c",
                severity=AlertSeverity.CRITICAL, metadata_json={})
            store.commit()
            r.record((time.perf_counter()-t0)*1000, True)
        except Exception:
            r.record((time.perf_counter()-t0)*1000, False)
    return r

def bench_ack(store, n):
    r = Result("Alert Ack")
    aids = []
    for i in range(n):
        store.begin_transaction()
        alert = store.create_alert(server_id="srv", alert_type=AlertType.HEALTH_CRITICAL,
            resource_type=ResourceType.SYSTEM, resource_id=f"ack-{i}", condition="c",
            severity=AlertSeverity.CRITICAL, metadata_json={})
        store.commit()
        aids.append(alert.alert_id)
    for aid in aids:
        t0 = time.perf_counter()
        try:
            store.begin_transaction()
            store.acknowledge_alert(aid, "user", "note")
            store.commit()
            r.record((time.perf_counter()-t0)*1000, True)
        except Exception:
            r.record((time.perf_counter()-t0)*1000, False)
    return r

def bench_res(store, n):
    r = Result("Alert Resolve")
    aids = []
    for i in range(n):
        store.begin_transaction()
        alert = store.create_alert(server_id="srv", alert_type=AlertType.HEALTH_CRITICAL,
            resource_type=ResourceType.SYSTEM, resource_id=f"res-{i}", condition="c",
            severity=AlertSeverity.CRITICAL, metadata_json={})
        store.acknowledge_alert(alert.alert_id, "user", "note")
        store.commit()
        aids.append(alert.alert_id)
    for aid in aids:
        t0 = time.perf_counter()
        try:
            store.begin_transaction()
            store.resolve_alert(aid, "resolved")
            store.commit()
            r.record((time.perf_counter()-t0)*1000, True)
        except Exception:
            r.record((time.perf_counter()-t0)*1000, False)
    return r

def run():
    print("="*80)
    print("PHASE 12K-A - SINGLE-CONNECTION BENCHMARK")
    print("="*80)
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"SQLite: {sqlite3.sqlite_version}")
    print("BEGIN: IMMEDIATE | busy_timeout: 5000ms | Lock retry: 3x0.1s")
    print(f"Warm-up: {WARMUP} | Measurement: {MEASUREMENT} | Rounds: {ROUNDS}")
    print()
    all_r = {"Transaction": [], "Alert Create": [], "Alert Ack": [], "Alert Resolve": []}
    try:
        for rnd in range(1, ROUNDS+1):
            print(f"=== ROUND {rnd}/{ROUNDS} ===")
            tmpdir = tempfile.mkdtemp()
            db = os.path.join(tmpdir, "bench.db")
            store = AlertStore(db)
            for _ in range(WARMUP):
                store.begin_transaction(); store.conn.execute("SELECT 1"); store.commit()
            for name, fn in [("Transaction", lambda: bench_tx(store, MEASUREMENT)),
                             ("Alert Create", lambda: bench_create(store, MEASUREMENT)),
                             ("Alert Ack", lambda: bench_ack(store, MEASUREMENT)),
                             ("Alert Resolve", lambda: bench_res(store, MEASUREMENT))]:
                res = fn()
                all_r[name].append(res)
                s = stats(res.samples)
                ops = res.ok / (res.elapsed/1000) if res.elapsed > 0 else 0
                print(f"  {name}: p50={s['p50']:.2f}ms p95={s['p95']:.2f}ms p99={s['p99']:.2f}ms {ops:.1f}ops/s")
            store.close()
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
            print()
    finally:
        pass
    print("="*80)
    print("AGGREGATE RESULTS")
    print("="*80)
    final = {"env": {"platform": sys.platform, "python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version}, "results": {}}
    for name, results in all_r.items():
        samples = [s for r in results for s in r.samples]
        s = stats(samples)
        ok = sum(r.ok for r in results)
        elapsed = sum(r.elapsed for r in results)
        ops = ok / (elapsed/1000) if elapsed > 0 else 0
        final["results"][name] = {"iterations": len(samples), "success": ok,
            "latency_ms": {k: round(v, 3) for k, v in s.items()}, "throughput_ops_per_sec": round(ops, 1)}
        print(f"{name}: p50={s['p50']:.2f}ms p95={s['p95']:.2f}ms p99={s['p99']:.2f}ms {ops:.1f}ops/s")
    with open(Path(__file__).parent / "benchmark_12k_a_samples.json", "w") as f:
        json.dump(final, f, indent=2)
    print()
    print("Status: 12K_A_COMPLETE")
    print("="*80)
    return final

if __name__ == "__main__":
    run()