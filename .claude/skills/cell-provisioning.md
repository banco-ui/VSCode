# Skill: USM Cell 증설 자동화

## 개요
CSV 템플릿 파일을 USM REST API로 전송하여 NE 내 Cell을 자동 증설합니다.

## 사전 조건
- NE가 이미 증설되어 있어야 함 (NE 증설 선행)
- USM MCM 서버 접근 가능 (10.251.209.131:7443)
- Cell 증설용 CSV 템플릿 파일 (섹션 기반 @SECTION 형식)

## 사용 방법

### 1. Dry-run (JSON 미리보기, API 호출 안 함)
```bash
node scripts/usm-cell-provisioning.js "<csv_file>" <ne_name> --dry-run
```

### 2. 실제 증설 (대화형 확인)
```bash
node scripts/usm-cell-provisioning.js "<csv_file>" <ne_name>
```

### 3. 자동 증설 (확인 생략)
```bash
node scripts/usm-cell-provisioning.js "<csv_file>" <ne_name> --auto
```

## CSV 템플릿 형식
NE 증설과 동일한 섹션 기반 형식:
```
"@CELL_INFORMATION"
"State","Cell Identity","Cell Num","Cell Name",...
"ADD","162","0","123",...
"ADD","172","1","133",...

"@CHANNEL_BOARD_INFORMATION"
"State","Unit Type","Unit ID","Board Type","Firmware Type"
"ADD","fcp","0","gcb1-c1a","type-none"

"@CPRI_PORT_INFORMATION"
"State","Unit Type","Unit ID","Port ID","CPRI Speed"
"ADD","fcp","0","0","10.1376-gbps"

"@RU_INFORMATION"
"State","RU Conf","RU Port ID","RU Unit Type","RU Board Type",...
"ADD","0_0_0","0","mmu","mt3205-780",...

"@SON_INFORMATION"
"Initial PCI","Initial RSI",...
"off","off",...
```

### 주요 섹션
- `@CELL_INFORMATION`: Cell 정보 (다중 행 가능)
- `@CHANNEL_BOARD_INFORMATION`: Channel Board 정보
- `@CPRI_PORT_INFORMATION`: CPRI Port 정보 (다중 행)
- `@RU_INFORMATION`: RU 정보 (다중 행)
- `@RU_CARRIER_PORT_INFORMATION`: RU Carrier Port 정보
- `@SON_INFORMATION`: SON 설정
- State가 `NONE`인 행은 자동으로 필터링됨

## API 스펙
- **URI**: `POST /oss/ne/{NE Name}/cells`
- **인증**: HTTPS Basic Auth (`ossuser:osspasswd`)
- **Content-Type**: `application/json`
- **타임아웃**: 300초 (Cell 증설은 NE 증설보다 오래 걸림)
- **응답**: `{ "RESULT": "OK" }` 또는 상세 메시지

## 주의사항
- Cell 증설은 NE 증설 이후에 진행해야 함
- API 응답 시간이 길 수 있음 (최대 300초)
- 이미 존재하는 Cell Identity로 증설 시 "already set" 메시지 반환

## 관련 파일
- 스크립트: `scripts/usm-cell-provisioning.js`
- 설정: `config/usm-config.json`
- 로그: `logs/provisioning.log`
- 리포트: `output/reports/`

## 성공 사례
- 2026-08-10: NVGNB_13172 Cell 3개 증설 (Cell Identity 162, 172, 182)
  - 첫 요청: 타임아웃(120s)이나 서버에서는 정상 처리됨
  - 두 번째 요청: "already set" 확인 → Cell이 정상 생성되었음을 확인
