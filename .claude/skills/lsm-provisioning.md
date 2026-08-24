# LSM LTE/eNodeB 증설 자동화 Skill

## 개요
LSM (LTE System Manager) 서버에 eNodeB NE 및 Cell을 증설하는 자동화 스크립트입니다.
JIO 사업자 환경의 LTE 장비 관리를 위해 개발되었습니다.

## 서버 정보
- **LSM IP**: 10.251.175.31
- **포트**: 7443 (HTTPS)
- **GUI URL**: https://10.251.175.31:7443/aceman/
- **GUI 계정**: qwerty / 1qaz@WSX
- **OSS API 계정**: (별도 확인 필요, 현재 GUI 계정 사용)

## 스크립트 위치
- **NE 증설**: `scripts/lsm-ne-provisioning.js`
- **Cell 증설**: `scripts/lsm-cell-provisioning.js`
- **설정 파일**: `config/lsm-config.json`

## 사용법

### NE 증설 (eNodeB)
```bash
# Dry-run (JSON 미리보기)
node scripts/lsm-ne-provisioning.js "enb_7550_lmd1.csv" --dry-run

# 실제 증설 (확인 포함)
node scripts/lsm-ne-provisioning.js "enb_7550_lmd1.csv"

# 자동 증설 (확인 없이)
node scripts/lsm-ne-provisioning.js "enb_7550_lmd1.csv" --auto
```

### Cell 증설 (LTE Cell)
```bash
# Dry-run (JSON 미리보기)
node scripts/lsm-cell-provisioning.js enb_7550 "cell_enb_7550_rf90_ph4.csv" --dry-run

# 실제 증설 (확인 포함)
node scripts/lsm-cell-provisioning.js enb_7550 "cell_enb_7550_rf90_ph4.csv"

# 자동 증설 (확인 없이)
node scripts/lsm-cell-provisioning.js enb_7550 "cell_enb_7550_rf90_ph4.csv" --auto
```

## CSV 템플릿 구조

### NE 증설 CSV (enb_xxxx_lmd1.csv 또는 enb_xxxx_guc2.csv)
18개 섹션으로 구성:
1. `@ENB` - NE 기본 정보 (NE ID, Type, Version 등)
2. `@SERVER_INFORMATION` - CFM/PSM 서버 정보
3. `@PLMN_INFORMATION` - MCC/MNC 정보
4. `@SON_INFORMATION` - SON 설정
5. `@MAIN_BOARD_INFORMATION` - 메인 보드 (lmd1-j5, guc2-d5 등)
6. `@EXTERNAL_LINK_INFORMATION` - 외부 링크
7. `@SYSTEM_SHARING_INFORMATION` - 시스템 공유
8. `@SYSTEM_LOCATION_INFORMATION` - 위치 정보
9. `@INTER_CONNECTION_INFORMATION` - 연동 정보
10. `@INTER_ENB_INFORMATION` - eNB 간 연결
11. `@CLOCK_INFORMATION` - 클럭 소스 (GPS)
12. `@PTP_INFORMATION` - PTP 설정
13. `@MME_INFORMATION` - MME 연결 정보
14. `@EXTERNAL_INTERFACE_INFORMATION` - 외부 인터페이스 (IPv6)
15. `@STATIC_ROUTE_INFORMATION` - 정적 라우팅
16. `@VIRTUAL_ROUTING_INFORMATION` - 가상 라우팅
17. `@VLAN_INFORMATION` - VLAN 설정
18. `@LAG_INFORMATION` - LAG 설정

### Cell 증설 CSV (cell_enb_xxxx_rf90_ph4.csv)
5개 섹션으로 구성:
1. `@CELL_INFORMATION` - LTE Cell 정보 (Earfcn DL/UL, PCI, Bandwidth 등)
2. `@NB_IOT_CELL_INFORMATION` - NB-IoT Cell 정보
3. `@CHANNEL_BOARD_INFORMATION` - 채널 보드 (ecp/lcc2-b5)
4. `@CPRI_PORT_INFORMATION` - CPRI 포트 (4910-mbps)
5. `@RU_INFORMATION` - RU 정보 (rf90-050 등)

## USM(NR) vs LSM(LTE) 차이점

| 항목 | USM (NR) | LSM (LTE) |
|---|---|---|
| NE 섹션 | `@NVGNB` | `@ENB` |
| Cell 섹션 | `@CELL_INFORMATION` (NR) | `@CELL_INFORMATION` (LTE) |
| 추가 섹션 | - | `@MME_INFORMATION`, `@NB_IOT_CELL_INFORMATION` |
| NE Type | NVGNB | macro_unified |
| 주파수 | earfcn (NR) | Earfcn DL/UL (LTE) |
| Board Type | NVGNB 보드 | lmd1-j5, guc2-d5 |
| RU Type | NR RU | rf90-050 등 |

## API 엔드포인트 (USM과 동일)
- `POST /oss/ne` - NE 증설
- `DELETE /oss/ne/{NE Name}` - NE 감설
- `POST /oss/ne/{NE Name}/cells` - Cell 증설
- `DELETE /oss/ne/{NE Name}/cells` - Cell 감설
- `GET /oss/neList` - NE 목록 조회
- `GET /oss/vnfcList` - VNFC 목록 조회

## 보드 타입별 템플릿
- **LMD1** (lmd1-j5): enb_xxxx_lmd1.csv
- **GUC2** (guc2-d5): enb_xxxx_guc2.csv

## RU 타입별 Cell 템플릿
- **RF90** (rf90-050): cell_enb_xxxx_rf90_ph4.csv
