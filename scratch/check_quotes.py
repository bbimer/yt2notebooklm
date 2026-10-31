import os

base = r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections"
for fname in ["01_sec1.md", "06_sec6.md"]:
    p = os.path.join(base, fname)
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    for l in text.splitlines():
        if "Сравнительная таблица" in l or "Матрица" in l:
            print(f"{fname}: {repr(l)}")
