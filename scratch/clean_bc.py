with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\Day_1_BATTLECARD.md", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Remove all emojis
text = text.replace("⚠️ ", "")
text = text.replace("⚡️ ", "")
text = text.replace("🎯 ", "")
text = text.replace("🎭 ", "")
text = text.replace("🚫 ", "")
text = text.replace("❌ ", "Запрещено: ")
text = text.replace("➔ ", "-> ")
text = text.replace(r"\$", "$")
text = text.replace("($\\Delta = 0$)", "(Δ = 0)")

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\Day_1_BATTLECARD.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated Day_1_BATTLECARD.md cleanly")

