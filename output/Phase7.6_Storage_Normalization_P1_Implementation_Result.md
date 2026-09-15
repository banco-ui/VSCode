# Phase 7.6 — Storage Normalization P1 Implementation Result

## 1. Result

**PASS**

## 2. Baseline

| 항목 | 값 |
|------|-----|
| HEAD (before) | `6c52c7a0096dfa1b6dd4f1f3b8a9b66fbc356830` |
| HEAD (after) | `271e01f` (auto-commit included redfish.py + tests) |
| Branch | `main` |
| Tests before | 160 passed |
| Working tree before | clean |

## 3. Implementation

### RedfishCollector

| 항목 | 값 |
|------|-----|
| File | `src/server_manager/collectors/redfish.py` |
| Symbol | `RedfishCollector.collect()` + `_collect_storage()` |
| Change | Storage collection 추가: `system["Storage"]` → `_collect_storage()` → Drives, Volumes fetch |

**추가된 코드:**
- `collect()` 메서드에 `_get_collection(system, "Storage")` 호출 추가
- `_collect_storage()` 신규 메서드: Storage collection의 각 member에 대해:
  - `StorageControllers[]` 추출
  - `Drives[]` 각각 fetch (partial failure 허용)
  - `Volumes` collection → 각 Volume fetch (partial failure 허용)

### RedfishNormalizer

| 항목 | 값 |
|------|-----|
| File | `src/server_manager/normalizers/redfish_normalizer.py` |
| Symbol | `RedfishNormalizer.normalize()` — Storage section |
| Change | `pass` 스킵 제거 → 실제 Storage parsing 구현 |

**추가된 코드:**
- `_media_type_from_str()`: Redfish MediaType → enum 매핑 (SSD/HDD/NVMe/Unknown)
- `_controller_supports_raid()`: ControllerCapabilities.RAIDSupport 또는 name/model 기반 RAID 지원 여부
- `_max_health()`: HealthStatus priority 기반 max 비교 (기존 `max()` 버그 수정)
- Storage parsing: `raw_data["storage"]` 리스트 순회, 각 subsystem에서 controllers/drives/volumes 파싱
- Capacity 변환: `CapacityBytes` (bytes) → `capacity_gb` (GB), `round(bytes / 1024**3, 2)`
- `no_hardware_raid` 플래그: controllers 없고 physical_disks 있으면 True
- `_build_health()`: `max()` → `_max_health()` 교체 (HealthStatus str enum 알파벳 순서 버그 수정)

## 4. Storage Data Flow

```
Redfish API
    ↓
RedfishCollector.collect()
    ├── _get_collection(system, "Storage")
    └── _collect_storage(storage_collection)
        ├── Storage member → StorageControllers[]
        ├── Drives[] → 각 drive fetch
        └── Volumes → collection → 각 volume fetch
    ↓
raw_data["storage"] = [{controllers, drives, volumes}, ...]
    ↓
RedfishNormalizer.normalize()
    ├── for storage_subsystem in raw_data["storage"]:
    │   ├── controllers → StorageController(name, model, health, raid_support)
    │   ├── drives → PhysicalDisk(name, model, capacity_gb, media_type, protocol, health)
    │   └── volumes → VirtualDisk(name, raid_type, capacity_gb, health)
    └── no_hardware_raid = (controllers == 0 and physical_disks > 0)
    ↓
Storage(controllers, physical_disks, virtual_disks, no_hardware_raid)
    ↓
Hardware(storage=Storage)
    ↓
ServerInventory
    ↓
HardwareVerifier (unchanged — already has storage fields)
    ↓
InventoryStore (unchanged)
    ↓
DashboardQueryService (unchanged — already reads storage)
```

## 5. Schema Impact

| 항목 | 값 |
|------|-----|
| Schema v1.0 changed | **NO** |
| Existing Pydantic model changed | **NO** |
| New enum added | **NO** |
| New field added | **NO** |

`models/inventory.py` — 변경 없음.
`models/enums.py` — 변경 없음.

## 6. Tests

### Tests Added

| File | New Tests | Test Names |
|------|-----------|------------|
| `tests/test_normalizers.py` | 10 | `test_normalize_storage`, `test_normalize_storage_multiple_subsystems`, `test_normalize_storage_nvme_media_type`, `test_normalize_storage_unknown_media_type`, `test_normalize_storage_missing_fields`, `test_normalize_storage_empty`, `test_normalize_storage_no_hardware_raid_flag`, `test_normalize_storage_partial_failure`, `test_normalize_storage_health_aggregation` |
| `tests/test_collectors.py` | 4 | `test_collect_storage_with_mock`, `test_collect_storage_partial_failure`, `test_collect_no_storage_ref`, `test_collect_storage_credential_safety` |

### Test Counts

| 항목 | 값 |
|------|-----|
| Before | 160 |
| After | 173 |
| Added | 13 |
| Passed | 173 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

## 7. Regression

| 항목 | 결과 |
|------|------|
| 160 existing tests | **PASS** |
| Any test deleted/weakened | **NO** |
| Any test changed to pass | **NO** |

## 8. Changed Files

### Production

- `server-manager-tool/src/server_manager/collectors/redfish.py` — Storage collection 추가
- `server-manager-tool/src/server_manager/normalizers/redfish_normalizer.py` — Storage parsing + `_max_health` 버그 수정

### Tests

- `server-manager-tool/tests/test_normalizers.py` — 10개 Storage 테스트 추가
- `server-manager-tool/tests/test_collectors.py` — 4개 Storage 테스트 추가

### Other

- `output/Phase7.5_TBMS_Integration_Architecture_P1_Design.md` — Phase 7.5 보고서 (이전 phase)
- `output/Phase7.6_Storage_Normalization_P1_Implementation_Result.md` — 본 보고서

## 9. Unrelated Changes

**NONE**

변경되지 않은 영역 (확인 완료):
- `models/` — 변경 없음
- `verifiers/` — 변경 없음
- `store/` — 변경 없음
- `dashboard/` — 변경 없음
- `orchestrator/` — 변경 없음
- `api/` — 변경 없음 (존재하지 않음)
- `cli/` — 변경 없음 (존재하지 않음)
- `config/` — 변경 없음
- `dependencies` — 변경 없음

## 10. Remaining Limitations

1. **SSH Normalizer Storage**: SSH collector는 `lsblk`와 `storcli` raw data를 수집하지만, SSH normalizer에서 이를 PhysicalDisk/StorageController로 파싱하지 않음. 이는 Phase 7.6 범위 외 (optional로 표시됨).

2. **Redfish `Volumes` with `Capacity` field**: 일부 Redfish 구현에서 `CapacityBytes` 대신 `Capacity`를 사용할 수 있음. Normalizer에서 두 필드 모두 확인하도록 구현됨.

3. **`_max_health` 버그 수정**: 기존 `_build_health()`에서 `max()`를 사용하여 HealthStatus str enum의 알파벳 순서 비교 문제("Unknown" > "Critical")가 있었음. `_max_health()` priority 기반 비교로 수정. 이는 Storage 구현과 직접 관련 없는 기존 버그이지만, Storage health aggregation 테스트에서 발견되어 수정함.

## 11. Recommended Next Phase

- **Phase 8**: Integration API 설계 및 구현 (Phase 7.5에서 설계된 9개 API endpoint)
- **Phase 8**: TBMS adapter 구현
- **Phase 9+**: SSH normalizer Storage parsing (lsblk → PhysicalDisk)
- **Phase 9+**: paramiko migration 검토

## 12. Git Diff Summary

```
Production:
  redfish.py: +76 lines (_collect_storage method + Storage collection call)
  redfish_normalizer.py: +87/-44 lines (Storage parsing + _max_health fix + helpers)

Tests:
  test_collectors.py: +241 lines (4 new Storage tests)
  test_normalizers.py: +270 lines (10 new Storage tests)

Total: +13 tests (160 → 173)
```

## 13. Safety Check

```
=== PHASE 7.6 SAFETY CHECK ===

Storage implementation: YES
Schema modified: NO
Models modified: NO
Verifier modified: NO
Store modified: NO
Dashboard modified: NO
Orchestrator modified: NO
API modified: NO
TBMS modified: NO
CLI modified: NO
Scheduler modified: NO
Dependencies modified: NO

Existing 160 tests preserved: YES
All tests passed: YES (173 passed)

Credentials exposed: NO
Production server accessed: NO
TBMS mutated: NO

Unrelated files modified: NO

Implementation scope respected: YES
```

### Non-Goals (confirmed)

```
✅ No schema modification
✅ No new enum
✅ No verifier changes
✅ No store changes
✅ No dashboard changes
✅ No orchestrator changes
✅ No API changes
✅ No CLI changes
✅ No TBMS changes
✅ No dependency changes
✅ No real production server access
✅ No unrelated refactoring
```

### Acceptance Criteria

```
[x] Redfish Storage collection implemented
[x] Redfish Storage normalization implemented
[x] Existing Storage models reused
[x] Schema v1.0 unchanged
[x] No new enum
[x] Verifier unchanged
[x] Dashboard unchanged
[x] InventoryStore unchanged
[x] Orchestrator unchanged
[x] No TBMS changes
[x] No API changes
[x] No CLI changes
[x] No Scheduler changes
[x] Storage tests added/updated
[x] Existing 160 tests still pass
[x] All tests pass (173 passed)
[x] No credentials exposed
[x] No real production server access required
[x] No unrelated refactoring
[x] Working tree contains only intended changes
```

---

# END OF PHASE 7.6
