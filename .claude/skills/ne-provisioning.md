# Skill: USM NE 증설 자동화

## 개요
CSV 템플릿 파일을 USM REST API로 전송하여 NE를 자동 증설합니다.

## 사전 조건
- USM MCM 서버 접근 가능 (10.251.209.131:7443)
- OSS 계정 (ossuser:osspasswd)
- NE 증설용 CSV 템플릿 파일 (섹션 기반 @SECTION 형식)

## 사용 방법

### 1. Dry-run (JSON 미리보기, API 호출 안 함)
```bash
node scripts/usm-ne-provisioning.js "<csv_file>" --dry-run
```

### 2. 실제 증설 (대화형 확인)
```bash
node scripts/usm-ne-provisioning.js "<csv_file>"
```

### 3. 자동 증설 (확인 생략)
```bash
node scripts/usm-ne-provisioning.js "<csv_file>" --auto
```

## CSV 템플릿 형식
섹션 기반 형식 (`@SECTION_NAME` → 헤더 → 데이터):
```
"@NVGNB"
"NE ID","NE Type","NE Version","NE Name",...
"13172","ns_gnb","26.A.0","NVGNB_13172",...

"@SERVER_INFORMATION"
"NE ID","CFM","PSM"
"","",""

"@IP_INFORMATION"
"NE ID","CPU ID","IP Address",...
"13172","0","100.254.13.172",...
```

## API 스펙
- **URI**: `POST /oss/ne`
- **인증**: HTTPS Basic Auth (`ossuser:osspasswd`)
- **Content-Type**: `application/json`
- **응답**: `{ "RESULT": "OK" }` (성공 시)

## 검증 방법
증설 후 NE List에서 확인:
```bash
curl -s -k -u "ossuser:osspasswd" "https://10.251.209.131:7443/oss/neList"
```

## 관련 파일
- 스크립트: `scripts/usm-ne-provisioning.js`
- 설정: `config/usm-config.json`
- 로그: `logs/provisioning.log`
- 리포트: `output/reports/`

## 성공 사례
- 2026-08-10: NVGNB_13172 (26.A.0) 증설 성공 (RESULT: OK)
