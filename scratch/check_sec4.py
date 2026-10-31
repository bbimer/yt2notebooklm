with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\04_sec4.md", "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines():
    if "###" in l or "Delphi" in l or "WLD" in l:
        print(l)

