with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\02_sec2.md", "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines()[50:]:
    print(l)

