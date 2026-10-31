with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\07_glossary.md", "r", encoding="utf-8") as f:
    text = f.read()

for i, l in enumerate(text.splitlines()):
    print(f"L{i+1}: {l}")

