with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\07_glossary.md", "r", encoding="utf-8") as f:
    text = f.read()

# Fix corrupted percentages
text = text.replace("$8080%", "80%")
text = text.replace("$\\pm 12.580%", "±12.5%")
text = text.replace("$96.480%", "96.4%")
text = text.replace("$10080%", "100%")
text = text.replace("$-16480%", "-164.25%")
text = text.replace("$9080%", "90%")
text = text.replace("$7070–90%", "70–90%")
text = text.replace("$4040–70%", "40–70%")

# Clean numbers and math
text = text.replace("$2^{256}-1$", "2²⁵⁶ - 1")
text = text.replace("($A$)", "(A)")
text = text.replace("$1:1$", "1:1")
text = text.replace("$\\text{Basis} = F - S$", "Basis = F - S")
text = text.replace("$P(d) = \\log_{10}(1 + 1/d)$", "P(d) = log₁₀(1 + 1/d)")
text = text.replace("$1.5$", "1.5")
text = text.replace("в $2$ раза", "в 2 раза")
text = text.replace("в $8$ раз", "в 8 раз")
text = text.replace("($\\text{LVR} \\propto \\sigma^2 (\\Delta t)^3$)", "(LVR ∝ σ² · (Δt)³)")
text = text.replace("нативном $ETH$", "нативном ETH")
text = text.replace("($P(t)$)", "(P(t))")
text = text.replace("$P(t) = P_0 \\cdot \\frac{M(t)}{M_0} \\cdot \\frac{S_0}{S(t)}$", "\n$$\nP(t) = P_0 \\cdot \\frac{M(t)}{M_0} \\cdot \\frac{S_0}{S(t)}\n$$\n")
text = text.replace("($\\Delta = 0$)", "(Δ = 0)")

with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\scratch\sections\07_glossary.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated 07_glossary.md cleanly")

