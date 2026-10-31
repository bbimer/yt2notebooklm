with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\05_sec5.md", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update subheadings
text = text.replace("### 5.1. Схема «The Insider Re-Lock»: Стейкинг залоченных токенов", "### 5.1. МЕТАФОРА: Схема «The Insider Re-Lock»: Стейкинг залоченных токенов")
text = text.replace("### 5.2. Судебные прецеденты манипулирования рынком в Web3", "### 5.2. КЕЙС: Судебные прецеденты манипулирования рынком в Web3")
text = text.replace("### 5.3. Спецоперация ФБР «Operation Token Mirrors» (Октябрь 2024 года)", "### 5.3. КЕЙС: Спецоперация ФБР «Operation Token Mirrors» (Октябрь 2024 года)")
text = text.replace("### 5.4. 📊 Числовой расчет и Unit-экономика иллюзии стейкинга (Депозиты $10,000 и $100,000)", "### 5.4. UNIT-ЭКОНОМИКА: Числовой расчет и Unit-экономика иллюзии стейкинга (Депозиты $10,000 и $100,000)")
text = text.replace("### 5.5. Ончейн-детекция манипуляций под капотом (Закон Бенфорда и кластерный анализ)", "### 5.5. ТЕХНИЧЕСКИЙ ПРУФ: Ончейн-детекция манипуляций под капотом (Закон Бенфорда и кластерный анализ)")
text = text.replace("### 5.6. 🎯 Прикладной скрипт закрытия (Индивидуальный подход по чеку)", "### 5.6. СКРИПТ ЗАКРЫТИЯ: Прикладной скрипт закрытия (Вектор А / Вектор Б)")

# 2. Clean pseudo-math
text = text.replace("Первая значащая цифра ($d$)", "Первая значащая цифра (d)")
text = text.replace("($\\Delta = 0$)", "(Δ = 0)")

# 3. Remove emojis
text = text.replace("📊", "")
text = text.replace("💥", "")
text = text.replace("🎯", "")
text = text.replace("💡", "")
text = text.replace("🔬", "")

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\05_sec5.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated 05_sec5.md cleanly")

