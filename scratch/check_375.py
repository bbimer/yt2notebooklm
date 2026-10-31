base = r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\01_sec1.md"
with open(base, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "375" in l:
        print(f"L{i+1}: {l.strip()}")

