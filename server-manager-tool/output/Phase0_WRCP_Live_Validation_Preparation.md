# Phase 0 — WRCP Live Validation Preparation

**Date**: 2026-10-14  
**Project**: D:\Data\AI\VSCode\server-manager-tool  
**Purpose**: WRCP 실환경 검증을 위한 사전 준비 (코드 수정 없음, 실제 접속 없음)

---

## 1. 현재 상태 요약

### 1.1 테스트 기준선

| 항목 | 결과 |
|------|------|
| **Passed** | 1,982 |
| **Skipped** | 27 |
| **Failed** | 1 (pre-existing: `test_is_due_past`) |
| **신규 회귀** | 0 건 |

### 1.2 구현 완료 항목 (Fixture/Mock 검증)

- ✅ StarlingX read-only Provider (6 REST + 3 CLI)
- ✅ StarlingX Normalizer (Platform, Cluster, Node)
- ✅ StarlingX Health Extractor (FM Alarm → Health)
- ✅ Kubernetes Provider (Node, Pod, PV/PVC)
- ✅ OpenStack Provider (Hypervisor, Server, Network, Volume)
- ✅ Redfish Collector (System, Processor, Memory, Storage)
- ✅ Canonical Domain Model (10 Entity)
- ✅ Graph Builder (DIRECT/DERIVED 관계)
- ✅ Health Assessment (HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN)
- ✅ Monitoring Service (Observation, StateChange)
- ✅ Fault Detection (5 FaultType, 3 Severity)
- ✅ Alert Service (OPEN→ACK→RESOLVED→CLOSED)
- ✅ Management API (Inventory, Health, Graph, Fault, Alert, Visibility)
- ✅ Dashboard (Overview, Inventory, Topology, Health, Faults/Alerts)

### 1.3 미구현 항목

- ❌ Redfish Physical ↔ StarlingX Node 자동 자산 연결
- ❌ USM REST API (port 5492) — 빈 응답 반환
- ❌ VIM REST API (port 4545) — Phase 29 이후
- ❌ 실제 WRCP Live 검증
- ❌ Recovery/Operations 실행 기능 (Preview 만)

---

## 2. 코드 검토 결과

### 2.1 StarlingX Provider — 읽기 전용 범위

**확인된 REST Endpoint (6 개)**:

| # | Endpoint | Port | 목적 | 쓰기 가능성 |
|---|----------|------|------|------------|
| 1 | `GET /v1/isystems` | 6385 | sysinv 시스템 정보 | ❌ 없음 |
| 2 | `GET /v1/ihosts` | 6385 | sysinv 호스트 정보 | ❌ 없음 |
| 3 | `GET /v1/ihosts/{uuid}/imemorys` | 6385 | sysinv 메모리 (sub-resource) | ❌ 없음 |
| 4 | `GET /v1/alarms` | 18002 | FM Alarm | ❌ 없음 |
| 5 | `GET /v1/event_log` | 18002 | FM Event Log | ❌ 없음 |
| 6 | `GET /v1/nodes/` | 7777 | SMAPI Node | ❌ 없음 |

**확인된 CLI Command (3 개)**:

| # | Command | 목적 | 쓰기 가능성 |
|---|---------|------|------------|
| 1 | `fm alarm-show <uuid>` | Alarm 상세 (7 CLI-only 필드) | ❌ 없음 |
| 2 | `system health-query` | 플랫폼 건강 상태 | ❌ 없음 |
| 3 | `software list` | USM 릴리스 정보 | ❌ 없음 |

**제외된 기능**:

- USM REST API (port 5492) — 유효한 토큰으로도 빈 응답
- VIM REST API (port 4545) — Phase 29 이후
- Write operations (acknowledge, lock/unlock, 등)

**안전 장치**:

```python
# Secret masking patterns
_SECRET_PATTERNS = [
    re.compile(r"(token['\":\s]+)([A-Za-z0-9\-_]{20,})", re.IGNORECASE),
    re.compile(r"(password['\":\s]+)(\S+)", re.IGNORECASE),
    re.compile(r"(X-Auth-Token['\":\s]+)(\S+)", re.IGNORECASE),
    re.compile(r"(secret['\":\s]+)(\S+)", re.IGNORECASE),
]
```

### 2.2 Redfish Collector — 인증 처리

**인증 방식**:

```python
def __init__(
    self,
    host: str,
    port: int = 443,
    username: str = "",
    password: str = "",
    use_ssl: bool = True,
    verify_ssl: bool = False,  # 기본값: 인증서 검증 안 함

---

## 3. 접속 전제조건

### 3.1 네트워크 요구사항

| 대상 | Port | 프로토콜 | 목적 |
|------|------|----------|------|
| WRCP AIO-SX | 6385 | HTTP | sysinv API |
| WRCP AIO-SX | 18002 | HTTP | FM API |
| WRCP AIO-SX | 7777 | HTTP | SMAPI API |
| WRCP AIO-SX | 22 | SSH | CLI (제한된 명령) |
| BMC (Redfish) | 443 | HTTPS | Redfish API |
| Kubernetes API | 6443 | HTTPS | K8s API (기존 권한) |

### 3.2 인증 요구사항

#### StarlingX (Keystone)

- **필요**: Keystone 토큰 (X-Auth-Token)
- **발급**: `POST /v3/auth/tokens` (Keystone)
- **만료**: 토큰 TTL 확인 (기본 24 시간)
- **권한**: sysinv, fm, smapi 읽기 전용

#### Redfish

- **필요**: BMC 사용자명/비밀번호
- **방식**: HTTP Basic Auth
- **TLS**: `verify_ssl=False` (기본값) — 변경 권장
- **권한**: System, Chassis, Manager 읽기 전용

#### Kubernetes

- **필요**: kubeconfig 또는 ServiceAccount 토큰
- **권한**: Node, Pod, PV/PVC 읽기 전용 (get, list)

### 3.3 시간 제한 및 재시도

| 설정 | 현재 값 | 권장 값 |
|------|---------|---------|
| HTTP Timeout | 30 초 | 30 초 (유지) |
| 재시도 | 미구현 | 최대 3 회, exponential backoff |
| 요청 수 제한 | 미정의 | 분당 60 요청 이하 |

---

## 4. Read-only 검증 범위 (초안)

### 4.1 Kubernetes

| Entity | 검증 항목 | HTTP 메서드 | 인증 |
|--------|----------|-------------|------|
| Node | 상태, 용량, 레이블 | GET | ServiceAccount |
| Pod | 상태, 리소스, 노드 | GET | ServiceAccount |
| PV/PVC | 상태, 용량, 바인딩 | GET | ServiceAccount |

**쓰기 가능성**: ❌ 없음 (GET 만)

### 4.2 StarlingX

| 데이터 | 검증 항목 | HTTP 메서드 | 인증 |
|--------|----------|-------------|------|
| sysinv isystems | 시스템 이름, 버전, 모드 | GET | Keystone 토큰 |
| sysinv ihosts | 호스트 이름, 가용성, bm_type | GET | Keystone 토큰 |
| sysinv imemorys | 메모리 용량 | GET (sub-resource) | Keystone 토큰 |
| FM alarms | Alarm ID, 심각도, 엔티티 | GET | Keystone 토큰 |
| FM event_log | 이벤트 이력 | GET | Keystone 토큰 |
| SMAPI nodes | 서비스 상태 | GET | Keystone 토큰 |

**CLI**:

| 명령 | 검증 항목 | 쓰기 가능성 |
|------|----------|------------|
| `fm alarm-show <uuid>` | Alarm 상세 필드 | ❌ 없음 |
| `system health-query` | 플랫폼 건강 상태 | ❌ 없음 |
| `software list` | USM 릴리스 | ❌ 없음 |

### 4.3 Redfish

| 리소스 | 검증 항목 | HTTP 메서드 | 인증 |
|--------|----------|-------------|------|
| System | 시리얼, 제조사, 모델 | GET | Basic Auth |
| Chassis | 섀시 타입, 위치 | GET | Basic Auth |
| Processor | CPU 수, 아키텍처 | GET | Basic Auth |
| Memory | DIMM 수, 용량 | GET | Basic Auth |
| Storage | 드라이브 수, 상태 | GET | Basic Auth |

**쓰기 가능성**: ❌ 없음 (GET 만)

### 4.4 통합 파이프라인

```
Provider 수집 (GET-only)
    ↓
Normalization (Canonical Entity)
    ↓
Inventory (CanonicalInventory)
    ↓
Graph (DIRECT/DERIVED 관계)

---

## 5. 중단 조건과 안전 규칙

### 5.1 즉시 중단 조건 (BLOCKED/FAIL)

다음 조건에서는 해당 검증을 즉시 중단합니다:

1. **인증정보 불명확**: 계정, 토큰, 권한 범위가 명시되지 않음
2. **읽기 전용 불가**: POST/PUT/PATCH/DELETE 요청이 필요함
3. **예상치 못한 쓰기**: GET 요청이 상태 변경을 유발함
4. **반복 요청 영향**: 요청 수 제한 초과 또는 시스템 부하 우려
5. **승인 범위 이탈**: 검증 대상이 승인된 엔드포인트를 벗어남
6. **민감정보 노출**: 응답에 토큰, 비밀번호, 키가 포함됨
7. **TLS 인증서 오류**: `verify_ssl=False` 필요 시 — 보안 위험

### 5.2 안전 규칙

1. **POST/PUT/PATCH/DELETE 금지**: Discovery 실행도 읽기 전용으로 제한
2. **CLI 명령 허용 목록**: 3 개 명령만 (`fm alarm-show`, `system health-query`, `software list`)
3. **토큰 마스킹**: 로그·보고서에 토큰 원문 기록 금지
4. **비밀번호 암호화**: kubeconfig, openrc, SSH 키 평문 저장 금지
5. **재시도 제한**: 최대 3 회, 백오프 필수
6. **요약 기록**: 원본 응답 대신 요약 데이터만 저장

---

## 6. 검증 시나리오 (초안)

### 6.1 인증 성공 및 실패

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| A1 | 유효한 Keystone 토큰으로 sysinv 조회 | 200 OK, 시스템 정보 반환 | `isystems` 리스트 비어있지 않음 |
| A2 | 만료된 토큰으로 FM 조회 | 401 Unauthorized | `errors['alarms']` 에 인증 실패 기록 |
| A3 | 유효한 BMC 인증으로 Redfish System 조회 | 200 OK, System 정보 반환 | `serialNumber` 필드 존재 |
| A4 | 잘못된 BMC 비밀번호 | 401 Unauthorized | 오류 메시지 반환 |

### 6.2 부분 장애 및 타임아웃

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| P1 | FM API 만 응답 불가 | 부분 수집 성공, `errors['alarms']` 기록 | 다른 엔드포인트는 정상 |
| P2 | sysinv 메모리 서브리소스 404 | 404 오류를 `errors['imemorys']` 로 기록 | 호스트 정보는 정상 수집 |
| P3 | API 응답 30 초 초과 | Timeout 오류 기록 | 재시도 3 회 후 실패 처리 |

### 6.3 Canonical ID 결정성

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| I1 | 동일한 host_uuid 로 2 회 수집 | 동일한 `canon-wrcp-node-{uuid}` 생성 | 2 회 결과 비교 |
| I2 | StarlingX 와 Kubernetes 노드 이름 동일 | 서로 다른 canonical_id (`canon-wrcp-*` vs `canon-kubernetes-*`) | namespace 분리 확인 |

### 6.4 UNKNOWN 및 누락 데이터

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| U1 | `availability` 필드 누락 | `UNKNOWN` 으로 설정, `HEALTHY` 로 변환 안 함 | HealthReport 확인 |
| U2 | `imemorys` 서브리소스 404 | 용량 0 이 아닌 `null` 또는 UNKNOWN | ResourceStatus 확인 |

### 6.5 자산 병합 방지

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| M1 | StarlingX Node 와 Redfish System 이름 동일 | 자동 병합 안 함 | `physicals` 와 `nodes` 분리 |
| M2 | IP 주소 동일 | 관계 생성 안 함 | Graph 에 INFERRED/UNKNOWN edge 없음 |

### 6.6 Fault/Alert 독립성

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| F1 | FM Critical Alarm 존재 | Node Entity 에 Fault 생성 | `fault_type=HEALTH_FAILURE` |
| F2 | Redfish Critical 상태 별도 존재 | Physical Entity 에 별도 Fault 생성 | `entity_id` 다름 |
| F3 | 동일 Fault 로 Alert 생성 | `alert_id` 결정적 생성 | 중복 Alert 없음 |

### 6.7 Graph 관계 유효성

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| G1 | Cluster → Node 관계 | `MEMBER_OF` edge 생성 | `evidence_type=DERIVED` |
| G2 | 이름/IP 기반 관계 | 생성 안 함 | INFERRED/UNKNOWN edge 없음 |

### 6.8 Management API/Dashboard

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| D1 | `/api/v1/inventory` 조회 | 200 OK, Entity 리스트 반환 | `physicals`, `nodes` 등 포함 |
| D2 | `/api/v1/health` 조회 | 200 OK, HealthReport 반환 | `UNKNOWN` 상태 포함 가능 |
| D3 | `/api/v1/faults` 조회 | 200 OK, Fault 리스트 반환 | FM 과 Redfish Fault 분리 |
| D4 | Dashboard Overview | Entity 카운트 표시 | API 결과와 일치 |

### 6.9 민감정보 비노출

| # | 시나리오 | 기대 결과 | 판정 기준 |
|---|----------|-----------|----------|
| S1 | API 응답 본문 | 토큰 원문 없음 | `_SECRET_PATTERNS` 매칭 안 함 |
| S2 | 로그 파일 | 비밀번호·토큰 마스킹됨 | `***` 또는 생략 |
| S3 | 브라우저 저장소 | kubeconfig·openrc 저장 안 됨 | DevTools 확인 |


---

## 7. 미확인 사항

### 7.1 접근 권한

- [ ] WRCP AIO-SX 관리망 IP 및 포트 개방 여부
- [ ] Keystone 토큰 발급 절차 및 만료 정책
- [ ] BMC IP 및 사용자 계정
- [ ] Kubernetes ServiceAccount 권한 범위

### 7.2 TLS/인증서

- [ ] StarlingX API 의 HTTPS 지원 여부 (현재 HTTP 포트 사용)
- [ ] Redfish 의 자체 서명 인증서 사용 여부
- [ ] `verify_ssl=False` 의 보안 허용 범위

### 7.3 API 버전

- [ ] WRCP 24.09 의 StarlingX 버전 (API 호환성)
- [ ] FM/Event Log 엔드포인트 경로 변경 가능성
- [ ] SMAPI API 버전

### 7.4 네트워크

- [ ] 관리망과 Server Manager 의 네트워크 격리 여부
- [ ] 방화벽 규칙 (인바운드/아웃바운드)
- [ ] 프록시 필요 여부

---

## 8. 실행 전 사용자 승인 필요 항목

다음 항목은 실제 실환경 검증 시작 전 사용자의 명시적 승인이 필요합니다.

### 8.1 인증정보 제공

- [ ] Keystone 토큰 발급 방법 (또는 사용자명/비밀번호)
- [ ] BMC (Redfish) 사용자명/비밀번호
- [ ] Kubernetes kubeconfig 또는 ServiceAccount 토큰

**주의**: 인증정보는 보고서나 로그에 기록하지 않습니다. 안전한 방법으로 전달하세요.

### 8.2 네트워크 접근 승인

- [ ] WRCP AIO-SX 관리망 접근 허용
- [ ] BMC 네트워크 접근 허용
- [ ] Kubernetes API 접근 허용

### 8.3 읽기 전용 범위 승인

- [ ] 6 개 REST Endpoint GET 만 허용
- [ ] 3 개 CLI 명령만 허용
- [ ] Discovery 실행은 읽기 전용으로 제한
- [ ] Operations/Recovery 실행 금지

### 8.4 보안 정책 승인

- [ ] `verify_ssl=False` 사용 허용 (권장: `True` 로 변경)
- [ ] 토큰 마스킹 처리
- [ ] 로그·보고서에 민감정보 비포함

### 8.5 중단 조건 승인

- [ ] 인증 실패 시 즉시 중단
- [ ] 예상치 못한 쓰기 감지 시 즉시 중단
- [ ] 민감정보 노출 시 즉시 중단

---

## 9. 다음 단계

### 9.1 승인 후 수행할 작업

1. **Phase 1 — 개별 Provider 연결 검증**
   - Redfish: System, Chassis, Processor, Memory 조회
   - StarlingX: sysinv, FM, SMAPI 조회
   - Kubernetes: Node, Pod, PV/PVC 조회

2. **Phase 2 — Discovery 및 정규화 검증**
   - Canonical Entity 생성 확인
   - SourceEvidence 보존 확인
   - UNKNOWN/누락 데이터 처리 확인

3. **Phase 3 — Health/Graph/Fault/Alert 검증**
   - Health 상태 판정 확인
   - Graph 관계 근거 확인
   - Fault/Alert 독립성 확인

4. **Phase 4 — Management API/Dashboard 검증**
   - Inventory/Health/Graph API 확인
   - Fault/Alert API 확인
   - Dashboard 화면 확인

5. **Phase 5 — 종단 간 검증**
   - 전체 파이프라인 연결 확인
   - 결과 보고서 작성

### 9.2 수행하지 않을 작업

- ❌ Phase 29 (USM/VIM API 확장)
- ❌ Redfish-StarlingX 자산 자동 연결 구현
- ❌ Recovery/Operations 실행
- ❌ Discovery 쓰기 요청
- ❌ 시스템 설정 변경 (kubeconfig, openrc, 등)

---

## 10. 결론

Phase 0 준비가 완료되었습니다. 현재 구현은 읽기 전용 검증에 충분하며, 안전 장치도 마련되어 있습니다.

**실환경 검증을 시작하려면 8 항의 승인 항목에 대한 사용자의 명시적 승인이 필요합니다.**

승인 후 Phase 1 (개별 Provider 연결 검증) 부터 단계별로 진행합니다. 각 단계에서 중단 조건이 발생하면 즉시 중단하고 결과를 기록합니다.

---

## 부록: 검증 가능한 엔드포인트 목록

### StarlingX REST (6 개)

```
GET http://{WRCP_IP}:6385/v1/isystems
GET http://{WRCP_IP}:6385/v1/ihosts
GET http://{WRCP_IP}:6385/v1/ihosts/{uuid}/imemorys
GET http://{WRCP_IP}:18002/v1/alarms
GET http://{WRCP_IP}:18002/v1/event_log
GET http://{WRCP_IP}:7777/v1/nodes/
```

### StarlingX CLI (3 개)

```
fm alarm-show {uuid}
system health-query
software list
```

### Redfish (HTTPS)

```
GET https://{BMC_IP}/redfish/v1/Systems
GET https://{BMC_IP}/redfish/v1/Chassis
GET https://{BMC_IP}/redfish/v1/Managers
```

### Kubernetes (HTTPS)

```
GET https://{K8S_API}:6443/api/v1/nodes
GET https://{K8S_API}:6443/api/v1/namespaces/{ns}/pods
GET https://{K8S_API}:6443/api/v1/persistentvolumes
GET https://{K8S_API}:6443/api/v1/persistentvolumeclaims
```

    ↓
Health (HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN)
    ↓
Monitoring (Observation, StateChange)
    ↓
Fault Detection (FaultType, Severity)
    ↓
Alert (OPEN → ACK → RESOLVED → CLOSED)
    ↓
Management API (GET /api/v1/*)
    ↓
Dashboard (조회 전용)
```

    timeout: int = 30,
) -> None:
```

**HTTP Basic Auth 사용**:

```python
creds = base64.b64encode(f"{username}:{password}".encode()).decode()
req.add_header("Authorization", f"Basic {creds}")
```

**주의사항**:

- `verify_ssl=False` 가 기본값 — 프로덕션 환경에서는 위험
- 인증 정보가 로그에 노출되지 않도록 마스킹 필요
- TLS 인증서 검증 정책 명시 필요

### 2.3 ManagementContext — 읽기 전용 보장

```python
class ManagementContext:
    """Holds pipeline service instances for the Phase 22 Management API.

    All services are read-only / preview-only:
        - No provider API calls
        - No shell commands or external process calls
        - No recovery executor invocation
        - No operation service invocation
        - No graph / health / fault mutation
    """
```
