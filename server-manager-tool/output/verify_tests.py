"""Phase 10D Test Verification Script"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

print("=" * 60)
print("TEST SOURCE VERIFICATION")
print("=" * 60)

with open('tests/test_scheduler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all test methods in TestPhase10DRecovery class
print("\n1. TestPhase10DRecovery Test Methods:")
expected_tests = [
    'test_recovery_clean_restart_no_stale',
    'test_recovery_running_execution_on_restart',
    'test_recovery_multiple_stale_executions',
    'test_recovery_missed_schedule_policy_skip',
    'test_recovery_idempotency',
    'test_recovery_with_sqlite_lock_retry',
    'test_recovery_duplicate_execution_protection',
    'test_recovery_metadata_persistence',
    'test_recovery_get_all_executions',
    'test_recovery_missed_schedule_policy_latest',
]

with open('tests/test_scheduler.py', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"\n   Checking TestPhase10DRecovery tests:")
found_count = 0
for test in expected_tests:
    if test in content:
        print(f"      [OK] {test}")
        found_count += 1
    else:
        print(f"      [FAIL] {test} - MISSING")

print(f"\n   Total: {found_count}/{len(expected_tests)} tests found")

# Check test_is_due_past
print("\n2. test_is_due_past Test:")
for i, line in enumerate(lines, 1):
    if 'def test_is_due_past' in line:
        print(f"   [OK] test_is_due_past found at line {i}")
        # Check which class it belongs to
        for j in range(i-1, max(0, i-50), -1):
            if lines[j].strip().startswith('class '):
                class_name = lines[j].strip().replace('class ', '').replace(':', '')
                print(f"   [INFO] Belongs to class: {class_name}")
                break
        break

print("\n" + "=" * 60)
print("GIT HISTORY CHECK")
print("=" * 60)

# Check git log for test_scheduler.py
import subprocess
try:
    result = subprocess.run(
        ['git', 'log', '--oneline', '--follow', '--', 'tests/test_scheduler.py'],
        capture_output=True, text=True, encoding='utf-8',
        cwd='d:\\Data\\AI\\VSCode\\server-manager-tool'
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')[:10]
        print(f"\n3. Last 10 commits affecting test_scheduler.py:")
        for line in lines:
            print(f"   {line}")
    else:
        print(f"   [WARN] git log failed: {result.stderr}")
except Exception as e:
    print(f"   [WARN] git check failed: {e}")

# Check git blame for test_is_due_past
try:
    result = subprocess.run(
        ['git', 'blame', '-L', '/test_is_due_past/,+10', '--', 'tests/test_scheduler.py'],
        capture_output=True, text=True, encoding='utf-8',
        cwd='d:\\Data\\AI\\VSCode\\server-manager-tool'
    )
    if result.returncode == 0:
        print(f"\n4. test_is_due_past git blame:")
        for line in result.stdout.strip().split('\n')[:3]:
            print(f"   {line}")
    else:
        print(f"   [INFO] git blame failed (may not exist in history)")
except Exception as e:
    print(f"   [WARN] git blame check failed: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("Test source verification complete.")