"""PHASE 12K-B - LINUX CONCURRENT CONTENTION BENCHMARK
Requirements: Linux environment (REQUIRED)
Usage: python benchmark_12k_b.py
"""
import json, os, sqlite3, sys, tempfile, time, uuid, threading
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from server_manager.alert.store import AlertStore
from server_manager.alert.models import AlertSeverity, AlertType, ResourceType

WORKERS = [2, 4, 8]
RUNS = 3
MEASUREMENT = 50

def pctl(d, p):
    if not d: return 0.0
    s = sorted(d); n = len(s); k = (n-1)*p/100; f = int(k); c = min(f+1, n-1)
    return s[f]*(c-k) + s[c]*(k-f) if f != c else s[f]

def stats(s):
    if not s: return {"min":0,"max":0,"mean":0,"std":0,"p50":0,"p95":0,"p99":0}
    return {"min":min(s),"max":max(s),"mean":mean(s),"std":stdev(s) if len(s)>1 else 0,
            "p50":pctl(s,50),"p95":pctl(s,95),"p99":pctl(s,99)}


def worker_same_fp(store, wid, barrier):
    result = WorkerResult(wid)
    try:
        barrier.wait(timeout=5)
        for i in range(MEASUREMENT):
            t0 = time.perf_counter()
            try:
                store.begin_transaction()
                store.create_alert(server_id="same-srv", alert_type=AlertType.HEALTH_CRITICAL,
                    resource_type=ResourceType.SYSTEM, resource_id="same-res", condition="same-cond",
                    severity=AlertSeverity.CRITICAL, metadata_json={"w": wid, "i": i})
                store.commit()
                result.record((time.perf_counter()-t0)*1000, "SUCCESS")
            except Exception as e:
                err = str(e).lower()
                if "duplicate" in err or "active alert" in err:
                    result.record((time.perf_counter()-t0)*1000, "DUPLICATE_PREVENTED")
                elif "locked" in err or "busy" in err:
                    result.record((time.perf_counter()-t0)*1000, "LOCK_WAIT")
                else:
                    result.record((time.perf_counter()-t0)*1000, f"ERROR:{err}")
    except Exception as e:
        result.record(0, f"BARRIER:{e}")
    return result

def worker_diff_fp(store, wid, barrier):
    result = WorkerResult(wid)
    try:
        barrier.wait(timeout=5)
        for i in range(MEASUREMENT):
            t0 = time.perf_counter()
            try:
                store.begin_transaction()
                store.create_alert(server_id="diff-srv", alert_type=AlertType.HEALTH_CRITICAL,
                    resource_type=ResourceType.SYSTEM, resource_id=f"diff-{wid}-{i}", condition="c",
                    severity=AlertSeverity.CRITICAL, metadata_json={"w": wid, "i": i})
                store.commit()
                result.record((time.perf_counter()-t0)*1000, "SUCCESS")
            except Exception as e:
                err = str(e).lower()
                if "locked" in err or "busy" in err:
                    result.record((time.perf_counter()-t0)*1000, "LOCK_WAIT")
                else:
                    result.record((time.perf_counter()-t0)*1000, f"ERROR:{err}")
    except Exception as e:
        result.record(0, f"BARRIER:{e}")
    return result

def check_db(db_path):
    store = AlertStore(db_path)
    cursor = store.conn.execute("SELECT status, COUNT(*) FROM alerts GROUP BY status")
    sc = {r[0]: r[1] for r in cursor.fetchall()}
    cursor = store.conn.execute("SELECT fingerprint, COUNT(*) as c FROM alerts WHERE status='OPEN' GROUP BY fingerprint HAVING c>1")
    dup = len(cursor.fetchall())
    store.close()
    return {"total": sum(sc.values()), "open": sc.get("OPEN",0), "ack": sc.get("ACKNOWLEDGED",0),
            "resolved": sc.get("RESOLVED",0), "dup_fp": dup}

def run_workload(wl, nw, db):
    barrier = threading.Barrier(nw)
    stores = [AlertStore(db) for _ in range(nw)]
    def fn(i):
        return (worker_same_fp if wl=="same_fp" else worker_diff_fp)(stores[i], i, barrier)
    with ThreadPoolExecutor(max_workers=nw) as ex:
        results = list(ex.map(fn, range(nw)))
    for s in stores: s.close()
    return results
class WorkerResult:
    def __init__(self, wid):
        self.wid, self.samples, self.status, self.elapsed = wid, [], [], 0.0
    def record(self, lat, status):
        self.samples.append(lat); self.elapsed += lat; self.status.append(status)

def run():
    import platform, shutil
    print("="*80 + "\nPHASE 12K-B - LINUX CONCURRENT CONTENTION BENCHMARK\n" + "="*80)
    is_linux = platform.system() == "Linux"
    print(f"Platform: {platform.system()}\nPython: {sys.version.split()[0]}\nSQLite: {sqlite3.sqlite_version}")
    if not is_linux:
        print("\n" + "="*80 + "\nWARNING: NOT LINUX\n" + "="*80)
        print("Results on Windows may not represent production concurrency.\n")
    print(f"CONFIG: Workers={WORKERS} | Runs={RUNS} | Iters={MEASUREMENT}\n")
    
    all_r = {"same_fp": {}, "diff_fp": {}}
    for wl in ["same_fp", "diff_fp"]:
        print("="*80 + f"\nWORKLOAD: {'SAME FP' if wl=='same_fp' else 'DIFF FP'}\n" + "="*80)
        for nw in WORKERS:
            print(f"\n--- Workers: {nw} ---")
            for run in range(1, RUNS+1):
                tmpdir = tempfile.mkdtemp()
                db = os.path.join(tmpdir, "bench.db")
                AlertStore(db).close()
                results = run_workload(wl, nw, db)
                correctness = check_db(db)
                samples = [s for r in results for s in r.samples]
                statuses = [st for r in results for st in r.status]
                s = stats(samples)
                sc = {}
                for st in statuses: sc[st] = sc.get(st, 0) + 1
                print(f"  Run {run}: p50={s['p50']:.2f}ms p95={s['p95']:.2f}ms | S:{sc.get('SUCCESS',0)} D:{sc.get('DUPLICATE_PREVENTED',0)} L:{sc.get('LOCK_WAIT',0)} | Open:{correctness['open']} DupFP:{correctness['dup_fp']}")
                if nw not in all_r[wl]: all_r[wl][nw] = []
                all_r[wl][nw].append({"run": run, "samples": samples, "statuses": statuses, "correctness": correctness, "stats": s})
                shutil.rmtree(tmpdir, ignore_errors=True)
    
    print("\n" + "="*80 + "\nSUMMARY\n" + "="*80)
    final = {"env": {"platform": platform.system(), "python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version},
             "config": {"workers": WORKERS, "runs": RUNS, "iterations": MEASUREMENT}, "results": all_r}
    for wl, wl_r in all_r.items():
        print(f"\n{wl.upper()}:")
        for nw, runs in wl_r.items():
            all_s = [s for r in runs for s in r["samples"]]
            s = stats(all_s)
            statuses = [st for r in runs for st in r["statuses"]]
            succ = sum(1 for st in statuses if st=="SUCCESS")
            dup = sum(1 for st in statuses if st=="DUPLICATE_PREVENTED")
            lock = sum(1 for st in statuses if st=="LOCK_WAIT")
            dup_fp = max(r["correctness"]["dup_fp"] for r in runs)
            print(f"  W={nw}: p50={s['p50']:.2f}ms p95={s['p95']:.2f}ms | S:{succ} D:{dup} L:{lock} | DupActiveFP:{dup_fp}")
    
    with open(Path(__file__).parent / "benchmark_12k_b_results.json", "w") as f:
        json.dump(final, f, indent=2)
    
    status = "12K_B_COMPLETE" if is_linux else "12K_B_COMPLETE_WITH_CONDITIONS (Windows)"
    print(f"\n{'='*80}\nStatus: {status}\n{'='*80}")
    if not is_linux: print("\nNOTE: Run on Linux for accurate results.")
    return final

if __name__ == "__main__":
    run()