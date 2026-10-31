with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\03_sec3.md", "r", encoding="utf-8") as f:
    text = f.read()

start = text.find("### 3.1.")
end = text.find("### 3.2.")
print(text[start:end])

