with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\Day_1_BATTLECARD.md", "r", encoding="utf-8") as f:
    text = f.read()

print("Lines count:", len(text.splitlines()))
for l in text.splitlines()[:60]:
    print(l)

