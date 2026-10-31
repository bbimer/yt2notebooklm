with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\02_sec2.md", "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines():
    if "Таблица" in l or "|" in l and ("RPC" in l or "Flashbots" in l or "Мемпул" in l):
        print(l)

