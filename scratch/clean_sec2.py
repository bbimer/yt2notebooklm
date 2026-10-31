import re

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\02_sec2.md", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update subheadings
text = text.replace("### 2.1. Эволюция комиссий: Математика EIP-1559 и экспоненциальный взрыв", "### 2.1. МЕТАФОРА: Эволюция комиссий и экспоненциальный взрыв EIP-1559")
text = text.replace("### 2.2. Архитектура PBS (Proposer-Builder Separation) и олигополия билдеров", "### 2.2. КЕЙС: Архитектура PBS (Proposer-Builder Separation) и олигополия билдеров")
text = text.replace("### 2.3. Защитные приватные шлюзы (Private RPC): Flashbots Protect и MEV-Blocker", "### 2.3. ТЕХНИЧЕСКИЙ ПРУФ: Защитные приватные шлюзы (Private RPC): Flashbots Protect и MEV-Blocker")
text = text.replace("### 2.4. Математика LVR (Loss-Versus-Rebalancing) и анатомия MEV-сэндвича", "### 2.4. UNIT-ЭКОНОМИКА: Математика LVR и анатомия MEV-сэндвича")
text = text.replace("### 2.5. Экономика прямых взяток билдерам (Builder Bribes & Direct Coinbase Transfers)", "### 2.5. ТЕХНИЧЕСКИЙ ПРУФ: Экономика прямых взяток билдерам (Builder Bribes & Direct Coinbase Transfers)")
text = text.replace("### 2.6. 🎯 Прикладной скрипт закрытия (Индивидуальный подход по чеку)", "### 2.6. СКРИПТ ЗАКРЫТИЯ: Прикладной скрипт закрытия (Вектор А / Вектор Б)")

# 2. Remove emojis and clean table symbols
text = text.replace("❌ Нет", "Нет")
text = text.replace("❌ 0%", "0%")
text = text.replace("✅ 100% защита", "100% защита (Да)")
text = text.replace("✅ До 90%", "До 90% (Да)")
text = text.replace("❌", "Нет")
text = text.replace("✅", "Да")
text = text.replace("⚠️", "Внимание:")
text = text.replace("💡", "")
text = text.replace("💥", "")
text = text.replace("📊", "")
text = text.replace("🔬", "")
text = text.replace("🎯", "")
text = text.replace("⚖️", "")
text = text.replace("⚖", "")

# 3. Clean pseudo-math and ranges
text = text.replace("$15\\text{M}$", "15M")
text = text.replace("$30\\text{M}$", "30M")
text = text.replace("$100\\%$", "100%")
text = text.replace("$1.0000\\times$", "1.0000x")
text = text.replace("$1.1250\\times$", "1.1250x")
text = text.replace("$1.2656\\times$", "1.2656x")
text = text.replace("$1.4238\\times$", "1.4238x")
text = text.replace("$1.8020\\times$", "1.8020x")
text = text.replace("$2.2807\\times$", "2.2807x")
text = text.replace("$3.2473\\times$", "3.2473x")
text = text.replace("$5.8518\\times$", "5.8518x")
text = text.replace("$10.5468\\times$", "10.5468x")
text = text.replace("$0.0\\%$", "0.0%")
text = text.replace("$+12.5\\%$", "+12.5%")
text = text.replace("$+26.6\\%$", "+26.6%")
text = text.replace("$+42.4\\%$", "+42.4%")
text = text.replace("$+80.2\\%$", "+80.2%")
text = text.replace("$+128.1\\%$", "+128.1%")
text = text.replace("$+224.7\\%$", "+224.7%")
text = text.replace("$+485.2\\%$", "+485.2%")
text = text.replace("$+954.7\\%$", "+954.7%")
text = text.replace("$8{,}000$", "8,000")
text = text.replace("$3{,}000--$6{,}000", "$3,000–$6,000")
text = text.replace("$100--$300", "100–300")
text = text.replace("$1--2$", "1–2")
text = text.replace("$1.4$", "1.4")
text = text.replace("$ETH$", "ETH")
text = text.replace("($\\Delta = 0$)", "(Δ = 0)")

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\02_sec2.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated 02_sec2.md cleanly")

