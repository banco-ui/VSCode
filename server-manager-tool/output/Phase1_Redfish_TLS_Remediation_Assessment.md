# Phase 1-RF.1 — Redfish TLS Remediation Assessment

**Date**: 2026-10-14  
**Project**: D:\Data\AI\VSCode\server-manager-tool  
**Status**: **진단 완료 — 서버별 TLS 오류 유형 구분됨**

---

## 1. 실행 개요

### 1.1 검증 대상 서버

| 서버 | iDRAC IP | 모델 |
|------|----------|------|
| Server 1 | 10.254.174.17 | Dell XR11 |
| Server 2 | 10.254.171.113 | Dell R750 |
| Server 3 | 10.254.170.196 | HPE e910t |

### 1.2 진단 방법

**스크립트**: `output/test_tls_diagnostic.py`

**진단 단계**:
1. TCP 443 포트 연결 테스트 (5 초 타임아웃)
2. TLS handshake with `verify=True` (SSL 인증서 검증)
3. 오류 유형 분류: `SSLCertVerificationError` 메시지 분석

**제한 사항**:
- Phase 29 시작 안 함
- 소스 코드 수정 안 함
- 서버 설정 변경 안 함
- `verify_ssl=False` 사용 안 함
- 인증정보 사용 안 함

---

## 2. 서버별 진단 결과

### 2.1 Dell XR11 (10.254.174.17)

| 항목 | 결과 |
|------|------|
| **TCP 443** | **OPEN** |
| **TLS handshake** | **FAIL** |
| **오류 유형** | **SELF-SIGNED CERTIFICATE** |

**진단**: 자체 서명 인증서 사용.

---

### 2.2 Dell R750 (10.254.171.113)

| 항목 | 결과 |
|------|------|
| **TCP 443** | **OPEN** |
| **TLS handshake** | **FAIL** |
| **오류 유형** | **SELF-SIGNED CERTIFICATE** |

**진단**: 자체 서명 인증서 사용.

---

### 2.3 HPE e910t (10.254.170.196)

| 항목 | 결과 |
|------|------|
| **TCP 443** | **OPEN** |
| **TLS handshake** | **FAIL** |
| **오류 유형** | **UNTRUSTED CA** |

**진단**: CA 서명 인증서 사용 but 신뢰 저장소에 없음.

---

## 3. 오류 유형 분석

### 3.1 자체 서명 (Dell XR11, R750)

**증상**: `self-signed certificate`

**원인**: Dell iDRAC 출고 시 자체 서명 인증서 사용.

**해결 방안**:
1. CA 발급 인증서로 교체 (권장)
2. 지문 검증 후 신뢰 등록 (차선)

---

### 3.2 신뢰할 수 없는 CA (HPE e910t)

**증상**: `unable to get local issuer certificate`

**원인**: 조직 내부 CA 서명 but Windows 신뢰 저장소에 없음.

**해결 방안**:
1. 조직 내부 CA 인증서 등록 (권장)
2. CA 번들 사용 (코드 수정 필요)

---

## 4. 해결 방안 비교

### 옵션 A: CA 발급 인증서 (권장 - Dell)

**장점**: 보안 강화, Phase 0.2 준수, 코드 수정 불필요  
**단점**: 구매 비용, 설치 작업

---

### 옵션 B: 조직 내부 CA 등록 (권장 - HPE)

**절차**:
```cmd
certutil -addstore -f "ROOT" <path-to-ca-cert>.crt
```

**장점**: 보안 유지, Phase 0.2 준수, 코드 수정 불필요  
**단점**: CA 인증서 파일, 관리자 권한 필요

---

### 옵션 C: 지문 검증 (차선 - Dell)

**절차**:
```bash
openssl s_client -connect 10.254.174.17:443 | openssl x509 -fingerprint -sha256
```

**장점**: CA 불필요  
**단점**: 수동 검증, 만료 시 재검증

---

## 5. 서버별 권장 조치

| 서버 | IP | 오류 | 권장 조치 | 관리자 |
|------|-----|------|----------|--------|
| Dell XR11 | 10.254.174.17 | SELF-SIGNED | CA 발급 또는 지문 검증 | 서버 관리자 |
| Dell R750 | 10.254.171.113 | SELF-SIGNED | CA 발급 또는 지문 검증 | 서버 관리자 |
| HPE e910t | 10.254.170.196 | UNTRUSTED CA | 내부 CA 등록 | 시스템 관리자 |

---

## 6. 인증서 지문 검증 절차

### 6.1 Dell iDRAC

```bash
openssl s_client -connect 10.254.174.17:443 -showcerts 2>nul | openssl x509 -fingerprint -sha256 -noout
```

### 6.2 HPE iLO

```bash
openssl s_client -connect 10.254.170.196:443 -showcerts 2>nul | openssl x509 -fingerprint -sha256 -noout
```

### 6.3 검증

1. 지문 확인
2. 서버 관리자와 비교 (안전한 채널)
3. 일치 시 신뢰 등록

---

## 7. 현재 구현 제한 사항

### 7.1 CA 번들 지정 불가

**현재 코드** (Line 194-198):
```python
ctx = ssl.create_default_context()
if not self.verify_ssl:
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
```

**제한**: 시스템 신뢰 저장소만 사용 가능.

---

## 8. 종합 판정

### 8.1 서버별 상태

| 서버 | IP | 오류 유형 | 권장 조치 | 상태 |
|------|-----|----------|----------|------|
| Dell XR11 | 10.254.174.17 | SELF-SIGNED | CA 발급/지문 | BLOCKED |
| Dell R750 | 10.254.171.113 | SELF-SIGNED | CA 발급/지문 | BLOCKED |
| HPE e910t | 10.254.170.196 | UNTRUSTED CA | 내부 CA 등록 | BLOCKED |

### 8.2 보안 조건 준수

| 항목 | 준수 |
|------|------|
| Phase 29 시작 안 함 | ✅ |
| 소스 코드 수정 안 함 | ✅ |
| 서버 설정 변경 안 함 | ✅ |
| `verify_ssl=False` 사용 안 함 | ✅ |
| 인증정보 사용 안 함 | ✅ |

---

## 9. 다음 단계

### 권장 시나리오

1. Dell: CA 발급 인증서 구매/설치
2. HPE: 조직 내부 CA 인증서 확보
3. Windows: `certutil` 로 신뢰 저장소 등록
4. Phase 1-RF 재실행

---

## 10. 결론

**Phase 1-RF.1** 은 서버별 TLS 오류 유형을 구분:

- **Dell XR11/R750**: 자체 서명 (SELF-SIGNED)
- **HPE e910t**: 신뢰할 수 없는 CA (UNTRUSTED CA)

**권장**: CA 인증서 등록 (코드 수정 없이 해결).

---

## 부록

**진단 스크립트**: `output/test_tls_diagnostic.py`

**결과**:
```
Dell XR11: TCP OPEN, TLS FAIL - SELF-SIGNED
Dell R750: TCP OPEN, TLS FAIL - SELF-SIGNED
HPE e910t: TCP OPEN, TLS FAIL - UNTRUSTED CA
```

**Git**: working tree clean ✅

**Phase 29**: 시작 안 함 ✅