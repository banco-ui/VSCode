# Phase 28H — Cross-Provider Integration & Contract Regression Validation

**Date**: 2026-10-14  
**Baseline**: Phase 28G 완료 (1947 passed, 27 skipped, 1 pre-existing failure)  
**Result**: 1982 passed, 27 skipped, 1 pre-existing failure (unchanged)

---

## 1. EXECUTIVE SUMMARY

Phase 28H는 Kubernetes, OpenStack, StarlingX, Redfish Provider 계약과 전체 통합 파이프라인의 회귀 안정성을 검증한다.

**핵심 결론:**
- 모든 Provider 계약(Kubernetes, OpenStack, StarlingX, Redfish)이 유지된다. ✓
- Canonical 모델과 Graph 안전성 규칙이 유지된다. ✓
- Health/Fault/Alert 생명주기와 식별 규칙이 유지된다. ✓
- Management API와 Dashboard의 기존 동작이 유지된다. ✓
- 읽기 전용 및 mutation safety 계약이 유지된다. ✓
- 기존 실패(`test_is_due_past`)는 신규 회귀가 아님을 확인했다. ✓
- **소스 코드 변경 불필요** — 신규 테스트 35개 추가만으로 모든 계약 검증 통과.

---

## 2. BASELINE CONFIRMATION

### 2.1 현재 저장소 상태

```
git status: tests/test_phase28h_cross_provider_regression.py (modified)
git log: 최근 scheduler 관련 변경 없음 (2026-09-21 이후 미변경)
```

### 2.2 테스트 결과 비교

| 항목 | Phase 28G 보고 | Phase 28H 실측 | 차이 |
|------|---------------|---------------|------|
| Total passed | 1947 | 1982 | +35 (신규 테스트) |
| Skipped | 27 | 27 | 0 |
| Failed | 1 (pre-existing) | 1 (pre-existing) | 0 |

---

## 3. PROVIDER별 검증 결과

### 3.1 Kubernetes Provider

| 검증 항목 | 상태 | 비고 |
|-----------|------|------|
| RawProviderSnapshot ↔ Normalizer 계약 일관성 | PASS | 기존 테스트 유지 |
| Canonical Entity 종류/의미 보존 | PASS | Node, Cluster, EE, Workload 등 |
| Canonical ID 결정적 생성 | PASS | `canon-kubernetes-{kind}-{ref}` |
| SourceEvidence 유지 | PASS | provider_type=KUBERNETES |
| UNKNOWN → HEALTHY 변환 방지 | PASS | 기존 테스트 커버 |
| API 오류/인증 실패/timeout 처리 | PASS | 기존 테스트 커버 |
| Provider 간 격리 | PASS | WRCP와 namespace 분리 확인 |

### 3.2 OpenStack Provider

| 검증 항목 | 상태 | 비고 |
|-----------|------|------|
| RawProviderSnapshot ↔ Normalizer 계약 일관성 | PASS | 기존 테스트 유지 |
| Canonical Entity 종류/의미 보존 | PASS | Platform, Cluster, Node 등 |
| Canonical ID 결정적 생성 | PASS | `canon-openstack-{kind}-{ref}` |
| SourceEvidence 유지 | PASS | provider_type=OPENSTACK |
| Provider 간 격리 | PASS | WRCP/K8s와 namespace 분리 확인 |

### 3.3 StarlingX (WRCP) Provider

| 검증 항목 | 상태 | 테스트 수 | 비고 |
|-----------|------|----------|------|
| Adapter 계약 (ProviderAdapter 상속, capabilities, collect) | PASS | 6 | TestStarlingXAdapterContract |
| Canonical ID 결정적 생성 | PASS | 4 | TestStarlingXDeterministicIds |
| SourceEvidence 보존 | PASS | 3 | TestStarlingXSourceEvidence |
| UNKNOWN → HEALTHY 변환 방지 | PASS | 2 | TestStarlingXNoUnknownToHealthy |
| Missing data → 0 변환 방지 | PASS | 1 | TestStarlingXNoMissingToZero |
| Graph 안전성 (INFERRED/UNKNOWN edge 금지) | PASS | 4 | TestStarlingXGraphSafety |
| Cross-provider 격리 | PASS | 4 | TestCrossProviderIsolation |
| Physical-Node 의미 분리 | PASS | 4 | TestPhysicalNodeSeparation |
| Partial failure 처리 | PASS | 2 | TestStarlingXPartialFailure |
| Fault/Alert lifecycle | PASS | 5 | TestStarlingXFaultAlertLifecycle |
| **소계** | **PASS** | **35** | |

### 3.4 Redfish Provider

| 검증 항목 | 상태 | 비고 |
|-----------|------|------|
| 기존 Collector/Normalizer 계약 | PASS | 기존 테스트 유지 |
| Physical entity 생성 (하드웨어 증거 기반) | PASS | 기존 테스트 유지 |
| StarlingX와의 자산 식별 분리 | PASS | Phase 28G 검증 결과 유지 |

### 3.5 Cross-Provider ID 격리 검증

```
StarlingX:  canon-wrcp-node-{host_uuid}       (namespace: wrcp)
Kubernetes: canon-kubernetes-node-{pod_ref}    (namespace: kubernetes)
OpenStack:  canon-openstack-node-{server_id}   (namespace: openstack)
```

동일한 `provider_ref`를 사용해도 namespace 접두사(`wrcp`/`kubernetes`/`openstack`)로 인해 canonical_id가 충돌하지 않는다.

---

## 4. CANONICAL 모델 및 GRAPH 검증 결과

### 4.1 Entity 의미 분리

| 규칙 | 상태 | 비고 |
|------|------|------|
| Node ≠ Physical | PASS | `canon-wrcp-node-*` ≠ `canon-wrcp-physical-*` |
| Workload ≠ ExecutionEnvironment | PASS | 기존 테스트 유지 |
| bm_type=none → Physical 미생성 | PASS | 4개 테스트로 검증 |
| bm_type=ipmi → Physical 미생성 (sysinv만으로) | PASS | Physical은 Redfish 하드웨어 증거 필요 |

### 4.2 Graph 안전성

| 규칙 | 상태 | 비고 |
|------|------|------|
| INFERRED edge 금지 | PASS | 4개 테스트로 검증 |
| UNKNOWN edge 금지 | PASS | evidence_type ∈ {DIRECT, DERIVED} |
| 관계 양 끝점 존재 확인 | PASS | graph.is_valid == True |
| 관계 중복 제거 시 출처 유지 | PASS | 기존 cross-provider 테스트 커버 |
| 이름/IP 기반 관계 추론 금지 | PASS | namespace 분리로 보장 |

---

## 5. HEALTH / MONITORING / FAULT / ALERT 검증 결과

| 검증 항목 | 상태 | 테스트 |
|-----------|------|--------|
| UNKNOWN → HEALTHY 변환 방지 | PASS | TestStarlingXNoUnknownToHealthy (2 tests) |
| Missing usage/capacity → 0 변환 방지 | PASS | TestStarlingXNoMissingToZero (1 test) |
| FM Critical과 Redfish Critical 독립 유지 | PASS | TestStarlingXFaultAlertLifecycle (5 tests) |
| Fault ID 중복 제거 일관성 | PASS | 동일 fault_id → 동일 alert_id |
| Alert lifecycle (OPEN→RESOLVED) | PASS | test_alert_can_be_resolved |
| 일부 Provider 실패 → 전체 정상 오인 방지 | PASS | TestCrossProviderIsolation (4 tests) |
| Operational Visibility 응답 유지 | PASS | 기존 테스트 유지 |

---

## 6. MANAGEMENT API / DASHBOARD 검증 결과

| 검증 항목 | 상태 | 비고 |
|-----------|------|------|
| Inventory 조회 | PASS | 기존 API 테스트 유지 |
| Health 조회 | PASS | 기존 API 테스트 유지 |
| Graph 및 Graph Summary 조회 | PASS | 기존 API 테스트 유지 |
| Fault 및 Alert 조회 | PASS | 기존 API 테스트 유지 |
| Operational Visibility 조회 | PASS | 기존 API 테스트 유지 |
| Discovery 실행 (읽기 전용) | PASS | 기존 API 테스트 유지 |
| Operations Preview (읽기 전용) | PASS | 기존 API 테스트 유지 |
| 오류 응답 형식 일관성 | PASS | 기존 API 테스트 유지 |
| 민감 정보 노출 방지 | PASS | 응답 스키마에 토큰/비밀번호 필드 없음 |

---

## 7. 안전성 계약 검증 결과

| 안전성 규칙 | 상태 | 비고 |
|------------|------|------|
| Provider 상태 변경 금지 | PASS | 모든 테스트가 fixture/mock 기반 |
| 자동 복구/재시도 추가 금지 | PASS | Recovery executor 미호출 |
| Recovery/Operations 실행 추가 금지 | PASS | Preview만 테스트 |
| 인증 정보 변경 금지 | PASS | 테스트용 fixture만 사용 |
| 실환경 POST/PUT/PATCH/DELETE 금지 | PASS | 읽기 전용 테스트만 |
| 민감 정보 로그 출력 금지 | PASS | 테스트에 토큰/비밀번호 없음 |

---

## 8. 전체 회귀 테스트 결과

### 8.1 최종 실행 결과

```
$ python -m pytest --tb=no -q
1982 passed, 27 skipped, 1 failed, 1 warning in 21.83s
```

### 8.2 Phase 28H 신규 테스트

```
$ python -m pytest tests/test_phase28h_cross_provider_regression.py --tb=short -q
35 passed in 5.35s
```

### 8.3 테스트 수 변화

| 항목 | Phase 28G 보고 | Phase 28H 실측 | 차이 |
|------|---------------|---------------|------|
| Total passed | 1947 | 1982 | +35 (Phase 28H 신규 테스트) |
| Skipped | 27 | 27 | 0 |
| Failed | 1 | 1 | 0 |
| 신규 회귀 | 0 | 0 | 0 |

---

## 9. 기존 실패와 신규 실패의 구분

### 9.1 실패한 테스트

```
FAILED tests/test_scheduler.py::TestScheduleDefinition::test_is_due_past
```

### 9.2 기존 실패 확인 근거

| 확인 항목 | 결과 |
|-----------|------|
| `tests/test_scheduler.py` 변경 이력 | Phase 28H 기간 중 변경 없음 |
| `src/server_manager/scheduler/` 변경 이력 | Phase 28H 기간 중 변경 없음 |
| 마지막 scheduler 관련 커밋 | 2026-09-21 (Phase 28H 이전) |
| `git diff` 결과 | scheduler 파일에 대한 변경사항 없음 |

### 9.3 결론

이 실패는 **기존 문제(pre-existing)**로 확인되었다. Phase 28H 작업 중 scheduler 관련 소스 코드나 테스트 파일이 전혀 수정되지 않았으므로, 신규 회귀가 아니다.

원인: `missed_policy` 필드의 기본값 동작 관련 기존 로직 문제. Phase 28H 범위가 아니며, 안전 제약상 이번 작업에서 수정하지 않는다.

---

## 10. 미해결 항목과 제한사항

### 10.1 Phase 28G에서 이월된 미해결 항목

| 항목 | 상태 | 비고 |
|------|------|------|
| Redfish Physical ↔ StarlingX Node 자동 자산 연결 | 미구현 | 권위 있는 교차 식별 증거 부족 |
| 시리얼/UUID 없는 경우 자산 추정 | 미구현 | 추론 기반 자산 연결 금지 |
| StarlingX sysinv 새로운 식별 정보 수집 | 미구현 | Phase 29 이후 검토 |
| USM/VIM API 확장 | 미구현 | Phase 29 범위 |

### 10.2 Phase 28H 제한사항

| 항목 | 내용 |
|------|------|
| Live validation | 실제 WRCP 환경 검증 미수행 (안전 제약) |
| Redfish 단독 검증 | 기존 테스트 재사용, 신규 테스트 추가 없음 |
| Dashboard UI | 코드 기반 검증, 실제 브라우저 렌더링 미검증 |

### 10.3 KNOWN_LIMITATIONS

- 모든 검증은 **fixture/mock 기반**이며, 실제 WRCP 24.09 AIO-SX 환경에서의 검증은 수행되지 않았다.
- `test_is_due_past` 실패는 기존 문제이며, Phase 28H 범위에서 수정하지 않는다.
- Redfish–StarlingX 교차 자산 식별은 권위 있는 식별 증거(시리얼, UUID 등)가 확보되기 전까지 자동 연결하지 않는다.
- Phase 29 (USM/VIM 쓰기 API)는 이번 단계에서 시작하지 않는다.

---

## 11. Fixture/Mock 검증과 Live 검증의 구분

### 11.1 Fixture/Mock 검증 (완료)

| 검증 영역 | 방식 | 테스트 수 |
|-----------|------|----------|
| StarlingX Provider 계약 | Synthetic fixture | 6 |
| Canonical ID 생성 | Synthetic fixture | 4 |
| SourceEvidence 보존 | Synthetic fixture | 3 |
| UNKNOWN 방지 | Synthetic fixture | 2 |
| Missing data 방지 | Synthetic fixture | 1 |
| Graph 안전성 | Synthetic fixture | 4 |
| Cross-provider 격리 | Synthetic fixture | 4 |
| Physical-Node 분리 | Synthetic fixture | 4 |
| Partial failure | Synthetic fixture | 2 |
| Fault/Alert lifecycle | Synthetic fixture | 5 |
| **총계** | | **35** |

### 11.2 Live 검증 (미수행)

| 항목 | 상태 | 사유 |
|------|------|------|
| WRCP 24.09 AIO-SX (10.254.174.70) | 미수행 | 안전 제약: 라이브 환경 변경 금지 |
| Redfish BMC 실제 조회 | 미수행 | 안전 제약: 인증 정보 사용 금지 |
| Kubernetes API 실제 조회 | 미수행 | 안전 제약: kubeconfig 변경 금지 |
| OpenStack API 실제 조회 | 미수행 | 안전 제약: openrc 변경 금지 |

**명확한 구분:** 이 보고서의 모든 검증은 fixture/mock 기반이다. Live validation을 완료했다고 표현하지 않는다.

---

## 12. Phase 28H 완료 판정

### 12.1 완료 기준 충족 여부

| # | 완료 기준 | 충족 | 비고 |
|---|----------|------|------|
| 1 | 기존 Provider 계약 유지 | ✅ PASS | K8s, OpenStack, StarlingX, Redfish 모든 계약 유지 |
| 2 | Canonical 모델/Graph 안전성 유지 | ✅ PASS | Node≠Physical, INFERRED/UNKNOWN edge 금지 |
| 3 | Health/Fault/Alert 생명주기 유지 | ✅ PASS | UNKNOWN→HEALTHY 방지, fault/alert lifecycle 독립성 |
| 4 | Management API/Dashboard 동작 유지 | ✅ PASS | 기존 API 테스트 전부 통과 |
| 5 | 신규 회귀 없음 | ✅ PASS | 신규 실패 0건 |
| 6 | 기존/신규 실패 구분 | ✅ PASS | scheduler 실패 = pre-existing 확인 |
| 7 | 읽기 전용/mutation safety 유지 | ✅ PASS | 모든 테스트 fixture/mock 기반 |

### 12.2 SOURCE_FILES_MODIFIED

| 파일 | 유형 | 내용 |
|------|------|------|
| `tests/test_phase28h_cross_provider_regression.py` | 신규 | 35개 cross-provider 회귀 테스트 (23,766 bytes) |
| `output/Phase28H_Cross_Provider_Integration_Contract_Regression_Validation.md` | 신규 | 본 보고서 |

**소스 코드 변경:** 없음 (소스 수정 불필요)

### 12.3 TEST_RESULTS

- Phase 28H 신규 테스트: **35 passed**
- 전체 회귀: **1982 passed, 27 skipped, 1 failed (pre-existing)**

### 12.4 REGRESSION_RESULTS

- 신규 회귀: **0건**
- 기존 실패: **1건** (`test_is_due_past` — scheduler, Phase 28H 이전부터 존재)

### 12.5 LIVE_VALIDATION_STATUS

**미수행** — 모든 검증은 fixture/mock 기반이다.

### 12.6 RECOMMENDED_NEXT_STEP

1. **Live validation (별도 작업)**: 안전 제약이 해제된 환경에서 WRCP 24.09 AIO-SX 실제 환경 검증
2. **Scheduler 실패 수정 (별도 작업)**: `test_is_due_past` 원인 분석 및 수정 — Phase 28H 범위 아님
3. **Phase 29**: USM/VIM 쓰기 API 확장 — 별도 phase에서 검토

### 12.7 최종 판정

**Phase 28H 완료**

모든 완료 기준(7/7)이 충족되었다. 신규 회귀 없음. 소스 코드 변경 없이 35개 신규 테스트만으로 모든 계약 검증을 통과했다. 기존 실패 1건은 scheduler 관련 기존 문제로 확인되었다.