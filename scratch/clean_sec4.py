with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\04_sec4.md", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update subheadings
text = text.replace("### 4.1. Исследование Delphi Digital: «The Curious Case of Token Unlocks»", "### 4.1. МЕТАФОРА: Исследование Delphi Digital: «The Curious Case of Token Unlocks»")
text = text.replace("### 4.2. Сравнительная таблица токенов цикла 2023–2025 годов и 5-фазный цикл разлока", "### 4.2. КЕЙС: Сравнительная таблица токенов цикла 2023–2025 годов и 5-фазный цикл разлока")
text = text.replace("### 4.3. Физика деривативного хеджирования: Почему 100% хедж на перпах НЕВОЗМОЖЕН", "### 4.3. ТЕХНИЧЕСКИЙ ПРУФ: Физика деривативного хеджирования: Почему 100% хедж на перпах НЕВОЗМОЖЕН")
text = text.replace("### 4.4. Математическая модель деградации цены от инфляции предложения", "### 4.4. UNIT-ЭКОНОМИКА: Математическая модель деградации цены от инфляции предложения")
text = text.replace("### 4.5. Вторичный внебиржевой рынок (Secondary OTC) и ликвидация риска", "### 4.5. ТЕХНИЧЕСКИЙ ПРУФ: Вторичный внебиржевой рынок (Secondary OTC) и ликвидация риска")
text = text.replace("### 4.6. 🎯 Прикладной скрипт закрытия (Индивидуальный подход по чеку)", "### 4.6. СКРИПТ ЗАКРЫТИЯ: Прикладной скрипт закрытия (Вектор А / Вектор Б)")

# 2. Clean pseudo-math and ranges
text = text.replace(r"\$60", "$60")
text = text.replace(r"\$10.00", "$10.00")
text = text.replace(r"\$100,000", "$100,000")
text = text.replace(r"\$10,000", "$10,000")
text = text.replace("$1.9\\%$", "1.9%")
text = text.replace("$84\\%$", "84%")
text = text.replace("$+320\\%$", "+320%")
text = text.replace("$350\\times$", "350x")
text = text.replace("$P_0 = \\$10.00$", "P₀ = $10.00")
text = text.replace("$P_0$", "P₀")
text = text.replace("$6.6$ млн", "6.6 млн")
text = text.replace("($\\Delta = 0$)", "(Δ = 0)")

# 3. Remove emojis
text = text.replace("🔬", "")
text = text.replace("💡", "")
text = text.replace("🎯", "")
text = text.replace("📊", "")
text = text.replace("💥", "")

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\04_sec4.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated 04_sec4.md cleanly")

