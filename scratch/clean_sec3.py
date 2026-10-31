with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\03_sec3.md", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update subheadings
text = text.replace("### 3.1. Анатомия резервов: Сравнение балансов Tether (USDT) и Circle (USDC)", "### 3.1. МЕТАФОРА: Анатомия резервов: Сравнение балансов Tether (USDT) и Circle (USDC)")
text = text.replace("### 3.2. Дюрационный риск и банковское заражение: Хроника краха SVB (Март 2023 года)", "### 3.2. КЕЙС: Дюрационный риск и банковское заражение: Хроника краха SVB (Март 2023 года)")
text = text.replace("### 3.3. Unit-экономика арбитража депега ($10,000 и $100,000) и протокол Circle CCTP", "### 3.3. UNIT-ЭКОНОМИКА: Арбитраж депега ($10,000 и $100,000) и протокол Circle CCTP")
text = text.replace("### 3.4. Математика Curve StableSwap: формула инварианта, оракулы и фазовый переход", "### 3.4. ТЕХНИЧЕСКИЙ ПРУФ: Математика Curve StableSwap: формула инварианта, оракулы и фазовый переход")
text = text.replace("### 3.5. Архитектура CDP-стейблкоинов и синтетиков (Maker PSM, LLAMMA, Ethena USDe)", "### 3.5. ТЕХНИЧЕСКИЙ ПРУФ: Архитектура CDP-стейблкоинов и синтетиков (Maker PSM, LLAMMA, Ethena USDe)")
text = text.replace("### 3.6. 🎯 Прикладной скрипт закрытия (Индивидуальный подход по чеку)", "### 3.6. СКРИПТ ЗАКРЫТИЯ: Прикладной скрипт закрытия (Вектор А / Вектор Б)")

# 2. Fix Table 3.1 missing amounts
text = text.replace("| **Капитализация (Cycle 2024–2025)** | **.3 млрд**", "| **Капитализация (Cycle 2024–2025)** | **$183.3 млрд**")
text = text.replace("| **.4 млрд** (разрыв в 2.5 раза) |", "| **$73.4 млрд** (разрыв в 2.5 раза) |")
text = text.replace("| От **,000** с комиссией 0.1% (,000). | От **,000** через", "| От **$100,000** с комиссией 0.1% ($1,000). | От **$100,000** через")

# 3. Fix range and percentages
text = text.replace("$1515–20%", "15–20%")
text = text.replace("$1515–25%", "15–25%")
text = text.replace(r"\$1.000", "$1.000")
text = text.replace(r"\$3.3 млрд", "$3.3 млрд")
text = text.replace(r"\$0.975", "$0.975")
text = text.replace(r"\$0.930", "$0.930")
text = text.replace(r"\$100,000", "$100,000")
text = text.replace(r"\$1,000,000", "$1,000,000")
text = text.replace("($\\Delta = 0$)", "(Δ = 0)")

# 4. Remove emojis
text = text.replace("📊", "")
text = text.replace("🎯", "")
text = text.replace("💡", "")
text = text.replace("💥", "")
text = text.replace("🔬", "")

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\03_sec3.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated 03_sec3.md cleanly")

