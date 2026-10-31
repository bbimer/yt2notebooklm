with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\src\research_academy\pipeline\synthesizer.py", "r", encoding="utf-8") as f:
    text = f.read()

start = text.find("def _build_day_1_battlecard")
print(text[start:start+1200])

