============================================================
PHASE 12 PRE-IMPLEMENTATION GATE — FINAL REPORT
============================================================

A. BASELINE
- Branch: main
- HEAD: 2f7d6fcba42ba514d2069d37fc7ca57a71390d78
- Working tree: CLEAN (no modifications)

B. TRANSACTION OWNERSHIP FINAL CHECK

결론: **ALERT_ENGINE**

이유:
1. AlertEngine 이 Scheduler 와의 external boundary (line 36-78)
2. AlertEngine.evaluate() 가 이미 try/catch 로 error boundary 관리
3. RuleEngine 은 pure business logic 에 집중 (transaction control 과 분리)
4. AlertStore 는 persistence abstraction (transaction control 노출 최소화)
5. 향후 Alert API 에서도 AlertEngine 이 transaction boundary 로 자연스러움
6. 현재 AlertEngine 이 AlertStore + RuleEngine 을 모두 소유 (line 32-34)

Flow:
```
AlertEngine.evaluate()
    ↓ BEGIN TRANSACTION
    RuleEngine.evaluate()
        ↓
        _is_snapshot_evaluated() → SELECT
        ↓
        _register_evaluation() → INSERT
        ↓
        _handle_failure() → Alert create/update
    ↓ COMMIT (on success) or ROLLBACK (on failure)
```

Implementation:
- AlertEngine.evaluate() 에서 transaction context 관리
- AlertStore 에 begin_transaction(), commit(), rollback() 추가
- RuleEngine 은 AlertStore 를 통해 transaction 사용

C. FINGERPRINT DEDUP FINAL CHECK

현재 schema:
- fingerprint: TEXT NOT NULL (UNIQUE constraint 없음)
- Index: idx_alerts_fingerprint (일반 index, UNIQUE 아님)
- Dedup: Application-level (create_alert line 240-249)

Lifecycle 요구사항:
- OPEN → ACKNOWLEDGED → RESOLVED
- RESOLVED 후 동일 condition 재발 → NEW OPEN alert 허용

질문: "단순 UNIQUE(fingerprint) 를 사용하면 RESOLVED 이후 재발 alert 생성과 충돌하는가?"

D. ALERT API AUTHORIZATION FINAL CHECK

현재 상태:
- Authorization foundation: **NONE**
- Inventory API: Open (internal-only 전제)
- Scheduler API: Open (internal-only 전제)
- FastAPI dependencies: Service wiring 만 (line 1-95)

충돌:
```
MUST HAVE: Alert API authorization model
PHASE 12.5 / LATER: Authorization layer
```

해석:
- "Authorization layer" = Full-blown auth system (OAuth2, RBAC, etc.)
- "Authorization model" = Minimal boundary for Alert API

질문:
A. 현재 authorization foundation 이 있는가? → **NO**
B. Alert API 를 먼저 구현하는 것이 architecture 상 안전한가? → **NO** (write operation 포함)
C. Authorization 을 Phase 12.5 로 미루고 Alert API 구현 가능한가? → **YES** (internal-only 전제)
D. 어느 수준의 authorization boundary 만 필요한가? → **Simple API key 또는 bearer token**

추천: **OPTION 2 — Minimal API authorization foundation 을 Phase 12 에서 먼저 구현**

이유:
1. Alert API 는 lifecycle transition (acknowledge, resolve) 포함 → write operation
2. Write operation 은 최소한의 authorization 필요 (internal-only 전제라도)
3. 기존 inventory/scheduler API 도 internal-only 이지만, Alert API 는 더 민감
4. Simple API key 기반 minimal auth layer 추가 (3-4 시간 작업)

E. API SCOPE 확인

현재 Alert lifecycle:
```
OPEN → ACKNOWLEDGED → RESOLVED
```

API 후보:
```
GET  /api/v1/alerts              # List (read-only)
GET  /api/v1/alerts/{id}         # Get (read-only)
POST /api/v1/alerts/{id}/ack    # Acknowledge (lifecycle transition)
POST /api/v1/alerts/{id}/resolve # Resolve (lifecycle transition)
GET  /api/v1/servers/{id}/alerts # Server-specific (read-only)
```

CRUD 필요성 검토:
- POST create: **NO** — System-generated alerts only (외부 CREATE 불허)
- PUT update: **NO** — Lifecycle transitions 만 허용 (ack, resolve)
- DELETE delete: **NO** — Alerts 는 soft-delete (resolve) 만 허용
- GET read: **YES** — Dashboard/query 용도

결론:

F. FINAL DECISION TABLE

| 항목 | 기존 Phase 12 결정 | 최종 결정 | 이유 |
|------|-------------------|-----------|------|
| Transaction owner | RuleEngine | **ALERT_ENGINE** | AlertEngine 이 external boundary, 이미 error boundary 관리 |
| Fingerprint dedup | INSERT OR IGNORE | **Option C (Atomic INSERT-if-not-exists)** | 현재 app-level dedup 유지, race condition 만 해결 |
| Fingerprint UNIQUE | 미확정 | **NO (application-level 유지)** | UNIQUE(fingerprint) 는 RESOLVED 후 재발 방지 (문제) |
| Partial unique index | 미확정 | **NO** | SQLite 복잡도 대비 이점 적음 |
| API authorization | Phase 12 / 12.5 충돌 | **Minimal auth in Phase 12** | Alert API write operation 에 최소 auth 필요 |
| Alert API CRUD | 제안 | **Lifecycle-based (NOT CRUD)** | System-generated alerts, lifecycle transitions 만 |

G. PHASE 12 IMPLEMENTATION ORDER

```
12A. AlertStore Transaction API
    ↓ (AlertStore 에 begin/commit/rollback 추가)
    
12B. AlertEngine Transaction Ownership
    ↓ (AlertEngine.evaluate() 가 transaction 관리)
    
12C. Fingerprint Atomic Dedup
    ↓ (INSERT OR IGNORE + affected rows check)
    
12D. Alert API Schemas + Routes
    ↓ (GET /alerts, GET /alerts/{id}, POST /ack, POST /resolve)
    
12E. Minimal Authorization
    ↓ (API key 기반 simple auth)
    
12F. Concurrency Tests
    ↓ (concurrent evaluation, fingerprint dedup)
    
12G. Crash/Recovery Tests
    ↓ (CASE B, C)
    
12H. Observability
    ↓ (Alert evaluation metrics/logging)
```

H. FINAL GATE

결론: **READY_FOR_PHASE_12_IMPLEMENTATION**

조건:
1. ✅ Transaction owner: AlertEngine (명확)
2. ✅ Fingerprint dedup: Option C (명확)
3. ✅ API authorization: Minimal auth in Phase 12 (명확)
4. ✅ API scope: Lifecycle-based, NOT CRUD (명확)

I. SAFETY

Production code modified: NO
Test code modified: NO
Schema modified: NO
Database modified: NO
API modified: NO
External server accessed: NO
TBMS accessed: NO
Credentials exposed: NO

============================================================
END OF PHASE 12 PRE-IMPLEMENTATION GATE
============================================================

- **CRUD 아님** — Lifecycle-based API
- Read-only GET endpoints
- POST acknowledge/resolve (lifecycle transitions)
- System-generated alerts 만 (외부 CREATE 불허)


답: **YES** — 단순 UNIQUE(fingerprint) 는 RESOLVED 된 후 재발 alert 생성을 막습니다.

후보 비교:
| Option | OPEN 중복 | ACK 중복 | RESOLVED 후 재발 | Concurrent | SQLite | Migration |
|--------|-----------|----------|-----------------|------------|--------|-----------|
| A: UNIQUE(fingerprint) | ❌ 방지 | ❌ 방지 | ❌ 방지 (문제) | ✅ | ✅ | ⚠️ |
| B: UNIQUE WHERE status IN ('OPEN','ACK') | ✅ 방지 | ✅ 방지 | ✅ 허용 | ✅ | ⚠️ 복잡 | ⚠️ |
| C: Atomic INSERT-if-not-exists | ✅ 방지 | ✅ 방지 | ✅ 허용 | ✅ | ✅ | ✅ |
| D: Application-level lock | ✅ 방지 | ✅ 방지 | ✅ 허용 | ⚠️ (single-process) | ✅ | ✅ |

추천: **Option C (Atomic INSERT-if-not-exists)**

이유:
1. 현재 application-level dedup logic 유지 (line 240-249)
2. INSERT OR IGNORE + affected rows check 로 race condition 해결
3. RESOLVED 후 재발 허용 (현재 동작과 호환)
4. SQLite 호환성 ✅
5. Migration 복잡도 낮음
