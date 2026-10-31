with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\06_sec6.md", "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines():
    if "###" in l or "``" in l:
        print(l)

