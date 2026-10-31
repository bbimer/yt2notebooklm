import re
from pathlib import Path

sec_dir = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections")

# 1. Fix 00_intro.md duplicate numbering
p_intro = sec_dir / "00_intro.md"
intro_text = p_intro.read_text(encoding="utf-8")
intro_text = intro_text.replace("1. `1. МЕТАФОРА:", "1. **МЕТАФОРА:")
intro_text = intro_text.replace("2. `2. КЕЙС:", "2. **КЕЙС:")
intro_text = intro_text.replace("3. `3. UNIT-ЭКОНОМИКА:", "3. **UNIT-ЭКОНОМИКА:")
intro_text = intro_text.replace("4. `4. ТЕХНИЧЕСКИЙ ПРУФ:", "4. **ТЕХНИЧЕСКИЙ ПРУФ:")
intro_text = intro_text.replace("5. `5. СКРИПТ ЗАКРЫТИЯ:", "5. **СКРИПТ ЗАКРЫТИЯ:")
# remove trailing backticks before colon
intro_text = intro_text.replace("(первые 30 сек)`:", "(первые 30 сек)**:")
intro_text = intro_text.replace("2023–2025)`:", "2023–2025)**:")
intro_text = intro_text.replace("$100,000)`:", "$100,000)**:")
intro_text = intro_text.replace("инварианты)`:", "инварианты)**:")
intro_text = intro_text.replace("Вектор Б)`:", "Вектор Б)**:")
p_intro.write_text(intro_text, encoding="utf-8")
print("Fixed 00_intro.md")

# 2. Fix 04_sec4.md table and math
p_sec4 = sec_dir / "04_sec4.md"
s4 = p_sec4.read_text(encoding="utf-8")
s4 = s4.replace("$+180\\%$", "+180%")
s4 = s4.replace("$+180%$", "+180%")
s4 = s4.replace("$+92\\%$", "+92%")
s4 = s4.replace("$+92%$", "+92%")
s4 = s4.replace("$+160\\%$", "+160%")
s4 = s4.replace("$+160%$", "+160%")
s4 = s4.replace("$+140\\%$", "+140%")
s4 = s4.replace("$+140%$", "+140%")
s4 = s4.replace("$280\\times$", "280x")
s4 = s4.replace("$280x$", "280x")
s4 = s4.replace("$60\\times$", "60x")
s4 = s4.replace("$60x$", "60x")
s4 = s4.replace("$190\\times$", "190x")
s4 = s4.replace("$190x$", "190x")
s4 = s4.replace("$85\\times$", "85x")
s4 = s4.replace("$85x$", "85x")
s4 = s4.replace("$1.5\\times\\dots 3.0\\times$", "1.5x–3.0x")
s4 = s4.replace("$M(t)$", "M(t)")
s4 = s4.replace("($M(t)/M_0$)", "(M(t) / M₀)")
s4 = s4.replace("($S(t)/S_0$)", "(S(t) / S₀)")
s4 = s4.replace("($P(t)$)", "(P(t))")
p_sec4.write_text(s4, encoding="utf-8")
print("Fixed 04_sec4.md")

# 3. Fix 05_sec5.md
p_sec5 = sec_dir / "05_sec5.md"
s5 = p_sec5.read_text(encoding="utf-8")
s5 = s5.replace(
    r"$$V_{\text{collateral}} = Q_{\text{MNGO}} \times P_{\text{manipulated}} = 488\text{M} \times $0.91 \approx $444\text{M}$$",
    r"$$V_{\text{collateral}} = Q_{\text{MNGO}} \times P_{\text{manipulated}} = 488\text{M} \times 0.91 \approx 444\text{M USD}$$"
)
s5 = s5.replace(r"($1{,}000$, $2{,}500$, $5{,}000$)", "(1,000, 2,500, 5,000)")
p_sec5.write_text(s5, encoding="utf-8")
print("Fixed 05_sec5.md")

