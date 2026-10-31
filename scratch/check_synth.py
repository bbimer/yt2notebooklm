with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\src\research_academy\pipeline\synthesizer.py", "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines():
    if "battlecard" in l.lower() or "generate" in l.lower():
        print(l)

