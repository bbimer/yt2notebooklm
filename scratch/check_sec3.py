import os

base = r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections"
p = os.path.join(base, "03_sec3.md")
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

for line in text.splitlines():
    if "Таблица 3.1" in line or ("USDT" in line and "|" in line) or "млрд" in line:
        print(line)
