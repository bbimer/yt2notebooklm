with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\src\research_academy\pipeline\synthesizer.py", "r", encoding="utf-8") as f:
    text = f.read()

# Replace _build_day_1_battlecard method
old_str = '''    def _build_day_1_battlecard(self) -> str:
        return r"""# ДЕНЬ 1. БОЕВАЯ ШПАРГАЛКА СЕЙЛЗА (BATTLECARD A4)'''

new_str = '''    def _build_day_1_battlecard(self) -> str:
        bc_path = self.exports_dir / "Day_1_BATTLECARD.md"
        if bc_path.exists():
            return bc_path.read_text(encoding="utf-8")
        return r"""# ДЕНЬ 1. БОЕВАЯ ШПАРГАЛКА СЕЙЛЗА (BATTLECARD A4)'''

if old_str in text:
    text = text.replace(old_str, new_str)
    with open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\src\research_academy\pipeline\synthesizer.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated synthesizer.py successfully!")
else:
    print("old_str not found!")

