with open('temp_original_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"=== Original Test File (Commit 3e10a67) ===")
print(f"Total lines: {len(lines)}")

tests = [l.strip() for l in lines if 'def test_' in l]
print(f"\nTest count: {len(tests)}\n")
for t in tests:
    print(t)

# Also count classes
classes = [l.strip() for l in lines if 'class Test' in l]
print(f"\nClass count: {len(classes)}")
for c in classes:
    print(c)