# Phase 1-RF.3 — Internal Management Network TLS Policy Review

**Date**: 2026-10-14  
**Project**: D:\Data\AI\VSCode\server-manager-tool  
**Status**: **조사 완료 — 대안 비교 및 권장안 제시**

---

## 1. 실행 개요

### 1.1 목표

내부 관리망에서 Redfish TLS 인증서 검증 정책을 결정하기 위한 근거 조사

### 1.2 대상 서버

| 서버 | IP | 모델 | TLS 오류 유형 |
|------|-----|------|-------------|
| Dell XR11 | 10.254.174.17 | XR11 | SELF-SIGNED |
| Dell R750 | 10.254.171.113 | R750 | SELF-SIGNED |
| HPE e910t | 10.254.170.196 | e910t | UNTRUSTED CA |

### 1.3 조사 방법

- **코드 분석**: `src/server_manager/collectors/redfish.py`
- **Python SSL 모듈 분석**: `ssl.create_default_context()` capabilities
- **제한 사항 준수**: 코드 수정 안 함, 실제 접속 안 함, 인증정보 사용 안 함

---

## 2. 현재 코드에서 확인한 사실

### 2.1 TLS 검증 설정

**위치**: `src/server_manager/collectors/redfish.py`

```python
# Line 29-42: __init__
def __init__(
    self,
    host: str,
    port: int = 443,
    username: str = "",
    password: str = "",
    use_ssl: bool = True,
    verify_ssl: bool = True,  # Phase 0.2: Default to True
    timeout: int = 30,
) -> None:
    ...
    self.verify_ssl = verify_ssl

# Line 194-198: _get_once
import ssl
ctx = ssl.create_default_context()
if not self.verify_ssl:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
```

**확인 사항**:
- `verify_ssl=True` 가 기본값 (Phase 0.2)
- `ssl.create_default_context()` 는 **시스템 신뢰 저장소만 사용**
- **CA 번들 파라미터 없음**

---

### 2.2 CA 번들 지원 여부

**Python `ssl` 모듈 분석 결과**:

```python
ctx = ssl.create_default_context()
print(hasattr(ctx, 'load_verify_locations'))  # True
print(inspect.signature(ctx.load_verify_locations))
# (cafile=None, capath=None, cadata=None)
```

**현재 구현**:
- ❌ `load_verify_locations()` 호출 없음
- ❌ `ca_bundle`, `cafile`, `capath` 파라미터 없음
- ❌ **애플리케이션 전용 CA 번들 미지원**

**결과**:
- 시스템 신뢰 저장소에 없는 CA 는 검증 실패
- 자체 서명 인증서는 무조건 실패

---

### 2.3 재시도 정책

**위치**: Line 133-179

**TLS 검증 실패 시 동작**:
```python
except Exception as e:
    # Unknown errors: don't retry, just log and return None
    logger.error("Redfish GET %s failed: %s", path, e)
    return None
```

**확인**: TLS 검증 실패는 재시도하지 않음 ✅

---

## 3. 대안 비교

### 3.1 대안 A: CA 발급 인증서 (외부 CA)

**개요**: Dell 에 공인 CA 인증서 구매, HPE 에 조직 내부 CA 확보

**장점**:
- ✅ 표준 TLS 검증 방식
- ✅ 코드 수정 불필요
- ✅ Phase 0.2 정책 준수
- ✅ MITM 차단

**단점**:
- ❌ CA 인증서 구매 비용 (DigiCert: 연 $100~500/서버)
- ❌ 서버별 설치 작업 (iDRAC/iLO 웹 UI)
- ❌ 갱신 주기 관리 (1~2 년)
- ❌ 내부망에 외부 CA 필요성 의문

**운영 부담**: 초기 1~2 시간/서버, 유지보수 연 1 회

---

### 3.2 대안 B: 조직 내부 CA 등록

**개요**: 조직 자체 CA 인증서를 Windows 신뢰 저장소에 등록

**구현**:
```cmd
certutil -addstore -f "ROOT" <ca-cert>.crt
```

**장점**:
- ✅ CA 구매 비용 없음
- ✅ 코드 수정 불필요
- ✅ 표준 TLS 검증 방식
- ✅ 내부망에 적합

**단점**:
- ❌ 내부 CA 인프라 필요
- ❌ 모든 클라이언트에 CA 등록 필요
- ❌ CA 유출 시 전체 신뢰 체계 붕괴

**운영 부담**: 초기 30 분~1 시간, 유지보수 5~10 년

---

### 3.3 대안 C: 애플리케이션 전용 CA 번들 (코드 수정 필요)

**개요**: 서버별 CA 인증서를 PEM 파일로 관리, 코드에서 로드

**구현** (최소 변경):
```python
# __init__ 에 추가
def __init__(self, ..., ca_bundle: Optional[str] = None):
    ...
    self.ca_bundle = ca_bundle

# _get_once 수정
ctx = ssl.create_default_context()
if self.ca_bundle:
    ctx.load_verify_locations(self.ca_bundle)
elif not self.verify_ssl:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
```

**장점**:
- ✅ 시스템 신뢰 저장소 영향 없음
- ✅ 서버별 CA 유연하게 관리
- ✅ 자체 서명 + CA 모두 지원
- ✅ 코드 수정 범위 작음 (5 줄)

**단점**:
- ❌ **코드 수정 필요** (Phase 1-RF.3 제한 사항 위반)
- ❌ CA 번들 파일 관리 필요

**운영 부담**: 초기 2~3 시간, 유지보수 인증서별

---

### 3.4 대안 D: 인증서 지문 고정 (Fingerprint Pinning)

**개요**: 각 서버의 인증서 SHA-256 지문을 설정에 저장, 연결 시 검증

**장점**:
- ✅ CA 불필요
- ✅ 자체 서명 인증서 사용 가능
- ✅ MITM 차단 (지문 불일치 감지)

**단점**:
- ❌ **코드 수정 필요** (더 복잡: ~30 줄)
- ❌ 초기 지문 확인 작업 필요 (수동)
- ❌ 인증서 갱신 시 지문 재확인 필요

**운영 부담**: 초기 30 분/서버, 유지보수 인증서별 높음

---

### 3.5 대안 E: TLS 검증 비활성화 (`verify_ssl=False`)

**개요**: `verify_ssl=False` 로 설정, 인증서 검증 생략

**장점**:
- ✅ 즉시 연결 가능
- ✅ 코드 수정 불필요 (이미 지원)
- ✅ CA 불필요

**단점**:
- ❌ **Phase 0.2 보안 강화 정책 위반**
- ❌ MITM 공격에 무방비
- ❌ 인증서 위조 감지 불가

**운영 부담**: 초기 5 분, 유지보수 없음

---

## 4. 대안 비교 요약

| 항목 | A: 외부 CA | B: 내부 CA | C: CA 번들 | D: 지문 고정 | E: 검증 비활성 |
|------|-----------|-----------|-----------|-------------|---------------|
| **코드 수정** | ❌ | ❌ | ✅ (5 줄) | ✅ (30 줄) | ❌ |
| **CA 비용** | ❌ $100~500/서버 | ✅ 무료 | ✅ 무료 | ✅ 무료 | ✅ 무료 |
| **초기 작업** | 1~2 시간/서버 | 30 분~1 시간 | 2~3 시간 | 30 분/서버 | 5 분 |
| **유지보수** | 연 1 회 | 5~10 년 | 인증서별 | 인증서별 높음 | 없음 |
| **MITM 차단** | ✅ 강함 | ✅ 강함 | ✅ 강함 | ⚠️ 중간 | ❌ 없음 |
| **내부망 적합** | ⚠️ 과할 수 있음 | ✅ 적합 | ✅ 적합 | ✅ 적합 | ❌ 위험 |
| **Phase 0.2 준수** | ✅ | ✅ | ✅ | ⚠️ | ❌ |

---

## 5. 권장안 및 근거

### 5.1 1 순위: 대안 B (조직 내부 CA 등록)

**근거**:
1. **내부망 특화**: 내부 CA 는 내부망에 가장 적합
2. **비용 효율**: CA 구매 불필요
3. **코드 수정 없음**: Phase 1-RF.3 제한 사항 준수
4. **표준 TLS**: Phase 0.2 정책 준수
5. **운영 단순**: CA 등록 후 자동 신뢰

**필요 조건**:
- 조직 내부 CA 존재 (또는 구축)
- CA 인증서 파일 확보 (.crt/.pem)
- Windows 신뢰 저장소 등록 권한

**실행 절차**:
1. HPE e910t 의 CA 인증서 파일 확보
2. Dell XR11/R750: 내부 CA 에서 새 인증서 발급 또는 지문 검증 후 등록
3. Windows: `certutil -addstore -f "ROOT" <ca-cert>.crt`
4. Phase 1-RF 재실행 (TLS 검증 통과 확인)

---

### 5.2 2 순위: 대안 C (CA 번들 지원 추가)

**근거**:
1. **유연성**: 서버별 CA 독립 관리
2. **코드 수정 작음**: 5 줄로 구현 가능
3. **시스템 영향 없음**: 신뢰 저장소 변경 없음
4. **미래 확장**: Kubernetes, StarlingX 도 동일 패턴 적용 가능

**필요 조건**:
- **Phase 1-RF.3 이후** 코드 수정 승인
- CA 번들 파일 준비
- 설정 파일 확장 (`ca_bundle` 경로)

**실행 절차**:
1. Phase 1-RF.3 보고서 승인
2. Phase 1-RF.4 로 코드 수정 (5 줄)
3. CA 번들 파일 준비 (`certs/` 디렉토리)
4. 설정 파일에 `ca_bundle` 경로 추가
5. 회귀 테스트 (13 개 신규 + 기존 1,995 개)
6. Phase 1-RF 재실행

---

### 5.3 비권장: 대안 E (TLS 검증 비활성화)

**근거**:
- Phase 0.2 보안 강화 정책과 정면 충돌
- 내부망이라도 MITM 위험 존재
- 인증정보 탈취 시 전체 관리망 침해

**사용 가능한 예외**:
- 개발/테스트 환경 (본격 운영 전)
- 네트워크 격리가 물리적으로 보장된 경우
- **단, 문서화하고 승인받아야 함**

---

## 6. 인증서 갱신 및 장애 복구

### 6.1 인증서 갱신 주기

| 대안 | 갱신 주기 | 관리 방법 |
|------|----------|----------|
| **A: 외부 CA** | 1~2 년 | CA 알림, 수동 교체 |
| **B: 내부 CA** | 5~10 년 (CA), 1~2 년 (서버) | 내부 CA 정책 |
| **C: CA 번들** | 서버별 상이 | PEM 파일 교체 |
| **D: 지문 고정** | 서버별 상이 | 수동 지문 재확인 |

### 6.2 장애 복구 절차

#### 대안 B/C: CA 인증서 만료

**증상**:
```
ssl.SSLCertVerificationError: certificate has expired
```

**복구**:
1. 서버: 새 인증서 발급/설치
2. 클라이언트: CA 번들 업데이트 (대안 C) 또는 자동 (대안 B)
3. 재시도 (재시도 로직 없음 — 수동 재실행)

#### 대안 D: 지문 불일치

**증상**:
```
SecurityError: Fingerprint mismatch
```

**복구**:
1. 새 인증서 지문 확인
2. 설정 파일 업데이트
3. 재실행

---

## 7. 구현 전 필요한 승인 사항

### 7.1 대안 B (내부 CA 등록) 선택 시

- [ ] 조직 내부 CA 존재 확인
- [ ] CA 인증서 파일 확보
- [ ] Windows 신뢰 저장소 등록 권한
- [ ] Dell XR11/R750: 내부 CA 로 재발급 또는 지문 검증

### 7.2 대안 C (CA 번들) 선택 시

- [ ] **Phase 1-RF.4 코드 수정 승인** (5 줄)
- [ ] CA 번들 파일 준비
- [ ] 설정 파일 확장 (`ca_bundle`)
- [ ] 회귀 테스트 계획 승인

### 7.3 공통

- [ ] Phase 1-RF 재실행 승인
- [ ] 실환경 연결 시험 승인 (읽기 전용)
- [ ] 결과 보고서 작성

---

## 8. 결론

### 8.1 현재 상태

- **Phase 0.2**: TLS 검증 활성화 (`verify_ssl=True`)
- **Phase 1-RF**: TLS 검증 실패로 BLOCKED
- **원인**: 시스템 신뢰 저장소에 서버 CA 없음

### 8.2 권장 해결 방안

**1 순위**: 대안 B (조직 내부 CA 등록)
- 코드 수정 불필요
- 내부망에 적합
- Phase 0.2 준수

**2 순위**: 대안 C (CA 번들 지원 추가)
- 코드 수정 5 줄
- 유연한 CA 관리
- 미래 확장성

### 8.3 다음 단계

1. **사용자/관리자 결정**: 대안 B 또는 C 선택
2. **필요한 자원 확보**:
   - 대안 B: CA 인증서 파일, 등록 권한
   - 대안 C: 코드 수정 승인, CA 번들 파일
3. **Phase 1-RF 재실행**: TLS 검증 통과 확인
4. **Phase 1-RF.4 (선택)**: 코드 수정 (대안 C 시)

---

## 9. 미확인 사항

### 9.1 조직 내부 CA

- **현재 상태**: 미확인
- **확인 필요**:
  - 조직이 자체 CA 운영 중인가?
  - CA 인증서 파일 (.crt/.pem) 확보 가능한가?
  - 내부 서버 인증서에 이미 서명되어 있는가?

### 9.2 네트워크 격리 수준

- **현재 상태**: 미확인
- **확인 필요**:
  - 10.254.x.x 대역이 외부 접근 완전히 차단된 내부망인가?
  - 세그먼트 간 방화벽 있는가?
  - MITM 공격 가능성 현실적인가?

### 9.3 `http://10.251.213.91:30080/` 서비스

- **현재 상태**: 미확인
- **Redfish TLS 정책과 직접 연결 안 함**
- **확인 필요**:
  - 이 서비스의 정체 (Kubernetes NodePort?)
  - HTTP 사용 이유
  - 내부망 접근만 가능한가?

---

**Phase 1-RF.3 조사 완료**. 대안 비교 및 권장안 제시됨.