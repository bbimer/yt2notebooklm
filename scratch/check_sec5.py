with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\05_sec5.md", "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines():
    if "###" in l or "Gotbit" in l or "Mango" in l:
        print(l)

