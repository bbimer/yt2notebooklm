import re
from pathlib import Path

sec_dir = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections")

def clean_section_pseudo_math(text: str) -> str:
    # 1. Tickers wrapped in $: $USDC$, $USDT$, $ETH$, $stETH$, $WETH$, $ETH-PERP$, $ETH/USDT$
    text = re.sub(r"\$(USDC|USDT|ETH|stETH|WETH|ETH-PERP|ETH/USDT|BTC|SOL|DAI|TIA|WLFI|crvUSD)\$", r"\1", text)
    
    # 2. Escaped dollar signs for currency: \$3,000 -> $3,000
    text = re.sub(r"\\\$(\d)", r"$\1", text)
    
    # 3. Percentages wrapped in $: $0.01\%$, $2\%$, $80--85\%$, $0.05\%$, $15--25\%$, $90\%$
    text = re.sub(r"\$(\d+(?:\.\d+)?)\\\%\$", r"\1%", text)
    text = re.sub(r"\$(\d+(?:\.\d+)?)\%\$", r"\1%", text)
    text = re.sub(r"\$(\d+)\-\-(\d+)\\\%\$", r"\1–\2%", text)
    text = re.sub(r"\$(\d+)\-\-(\d+)\%\$", r"\1–\2%", text)
    
    # 4. Plain numbers wrapped in $ that are NOT currency (e.g. $0.001$, $0.25$, $0.0156$, $0.4$, $0.064$, $2.0$, $8.0$, $12.0$, $1728.0$, $12$)
    # Be careful not to match $10,000 or $100,000 or $1k or $50k
    numbers_to_unwrap = [
        "0.001", "0.25", "0.0156", "0.4", "0.064", "2.0", "8.0", "12.0", "1728.0",
        "12", "175.74", "900", "180", "8.33"
    ]
    for num in numbers_to_unwrap:
        text = text.replace(f"${num}$", num)
    
    # 5. Clean common formulas in prose:
    text = text.replace("$1:1$", "1:1")
    text = text.replace("$n=3$", "n = 3")
    text = text.replace("$x + y = C$", "(x + y = C)")
    text = text.replace("$x + y = D$", "(x + y = D)")
    text = text.replace("$x \\cdot y = k$", "(x · y = k)")
    text = text.replace("$x y = k$", "(x · y = k)")
    text = text.replace("$A=100$", "A = 100")
    text = text.replace("$A=2000$", "A = 2000")
    text = text.replace("($\\Delta = 0$)", "(Δ = 0)")
    text = text.replace("$\\Delta = 0$", "Δ = 0")
    text = text.replace("(\\Delta = 0)", "(Δ = 0)")
    text = text.replace("($\\Delta t$)", "(Δt)")
    text = text.replace("(\\Delta t)", "(Δt)")
    text = text.replace("$(\\Delta t)^3$", "(Δt)³")
    text = text.replace("(\\Delta t)^3", "(Δt)³")
    text = text.replace("Объем свопа ($)", "Объем свопа (USD)")
    text = text.replace("$3--5$", "3–5")
    text = text.replace("$P_0 = $10.00$", "P₀ = $10.00")
    text = text.replace("$P_0 = $", "P₀ = ")
    text = text.replace("$10$ раз", "10 раз")
    text = text.replace("$20$ блоков", "20 блоков")
    text = text.replace("$50$ и $60$", "50 и 60")
    text = text.replace("$1$ блок", "1 блок")
    text = text.replace("Виснет на $", "Виснет на 15 минут")
    text = text.replace("от $2", "от 2%")
    
    # Clean single letter variables like $A$, $D$, $n$, $K$, $t$, $V$, $S$
    for var in ["A", "D", "n", "K", "t", "V", "S"]:
        text = re.sub(rf"\${var}\$", var, text)
        
    return text

for f in sorted(sec_dir.glob("*.md")):
    content = f.read_text(encoding="utf-8")
    cleaned = clean_section_pseudo_math(content)
    if cleaned != content:
        f.write_text(cleaned, encoding="utf-8")
        print(f"Cleaned {f.name}")

print("Sections cleanup complete.")

