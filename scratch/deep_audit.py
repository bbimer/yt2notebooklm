import os, re

base = r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections"
emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]")

for fname in sorted(os.listdir(base)):
    p = os.path.join(base, fname)
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    
    emojis_found = set(emoji_pattern.findall(text))
    has_375 = "375" in text
    bad_quotes = re.findall(r'["\']####.*', text)
    bad_ranges = re.findall(r'\$\d{2,}\d{2,}[x%–-]', text)
    bad_percentages = re.findall(r'\d+80%', text)
    
    print(f"=== {fname} ===")
    print(f"  Emojis: {emojis_found}")
    print(f"  Has 375: {has_375}")
    print(f"  Bad quotes before H4: {bad_quotes}")
    print(f"  Bad ranges: {bad_ranges}")
    print(f"  Bad percentages: {bad_percentages}")

