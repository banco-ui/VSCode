with open('src/server_manager/alert/store.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines 165-185:")
for i, line in enumerate(lines[165:185], start=165):
    print(f"{i}: {line}", end='')

print("\n\nLines 185-200:")
for i, line in enumerate(lines[185:200], start=185):
    print(f"{i}: {line}", end='')
