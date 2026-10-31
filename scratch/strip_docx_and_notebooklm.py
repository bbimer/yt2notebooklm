from pathlib import Path

synth_path = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\src\research_academy\pipeline\synthesizer.py")
text = synth_path.read_text(encoding="utf-8")

# Let's normalize synthesize_day_1_pack
start_marker = "    def synthesize_day_1_pack(self) -> Dict[str, Path]:"
end_marker = "    def _build_day_1_battlecard(self) -> str:"

p1 = text.find(start_marker)
p2 = text.find(end_marker)

new_method = '''    def synthesize_day_1_pack(self) -> Dict[str, Path]:
        """
        Executes clean synthesis for Day 1:
        1. Day_1_BATTLECARD.md -> Day_1_Battlecard.pdf (strictly 2-page A4 cheat sheet for calls)
        2. Day_1_Sales_Playbook.md -> Day_1_Sales_Playbook.pdf (full textbook 1,200-1,500 lines)
        """
        battlecard_md = self._build_day_1_battlecard()
        battlecard_path = self.exports_dir / "Day_1_BATTLECARD.md"
        battlecard_path.write_text(battlecard_md, encoding="utf-8")

        playbook_md = self._build_day_1_playbook()
        playbook_path = self.exports_dir / "Day_1_Sales_Playbook.md"
        playbook_path.write_text(playbook_md, encoding="utf-8")

        # Render PDF
        battlecard_pdf = self.renderer.render_pdf(
            markdown_path=battlecard_path,
            output_pdf_path=self.exports_dir / "Day_1_Battlecard.pdf",
            title="День 1: Шпаргалка для звонка (Battlecard A4)",
            subtitle="Модуль M/01: Токеномика, депег стейблкоинов и архитектура сетей",
            is_battlecard=True,
        )

        playbook_pdf = self.renderer.render_pdf(
            markdown_path=playbook_path,
            output_pdf_path=self.exports_dir / "Day_1_Sales_Playbook.pdf",
            title="Корпоративный учебник по крипторынку (Sales Playbook)",
            subtitle="Модуль M/01: Хищная токеномика, физика депега и судебная хроника манипуляций",
            is_battlecard=False,
        )

        return {
            "battlecard_md": battlecard_path,
            "battlecard_pdf": battlecard_pdf,
            "playbook_md": playbook_path,
            "playbook_pdf": playbook_pdf,
        }

'''

text = text[:p1] + new_method + text[p2:]
synth_path.write_text(text, encoding="utf-8")
print("Updated synthesizer.py without docx and master notebooklm")

# Delete docx and master notebooklm
pack = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack")
for f in [pack / "Day_1_Sales_Playbook.docx", pack / "Day_1_MASTER_NOTEBOOKLM.md"]:
    if f.exists():
        f.unlink()
        print(f"Deleted: {f.name}")

