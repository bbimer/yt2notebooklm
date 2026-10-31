import re

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\Day_1_BATTLECARD.md", "r", encoding="utf-8") as f:
    text = f.read()

emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]")
emojis = set(emoji_pattern.findall(text))
print("Battlecard Emojis:", emojis)
print("Battlecard size:", len(text))
print("First 5 lines:")
for l in text.splitlines()[:5]:
    print(l)

