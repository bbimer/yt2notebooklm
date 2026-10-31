with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\03_sec3.md", "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines():
    if "###" in l or "Таблица" in l or "млрд" in l or "180%" in l or "1515" in l:
        print(l)

