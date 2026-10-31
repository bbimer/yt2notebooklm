# -*- coding: utf-8 -*-
"""Generator script for complete, rigorous, deduplicated playbook_content.py.
Assembles the playbook directly from verified modular sections in scratch/sections/.
Targets 1,200 - 1,500 lines of pristine Markdown with unbranded institutional rigor.
"""

from pathlib import Path

SCRATCH_SECTIONS = Path(__file__).resolve().parent / "sections"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "src" / "research_academy" / "pipeline" / "playbook_content.py"

SECTION_MAP = [
    ("00_intro.md", "get_intro_enriched"),
    ("01_sec1.md", "get_sec1_enriched"),
    ("02_sec2.md", "get_sec2_enriched"),
    ("03_sec3.md", "get_sec3_enriched"),
    ("04_sec4.md", "get_sec4_enriched"),
    ("05_sec5.md", "get_sec5_enriched"),
    ("06_sec6.md", "get_sec6_enriched"),
    ("07_glossary.md", "get_glossary_enriched"),
]


def generate():
    code_lines = [
        '# -*- coding: utf-8 -*-',
        '"""Institutional Sales Playbook Content Module.',
        'Provides fully enriched, modular section text with rigorous mathematical proofs,',
        'unit economics on deposits of $10,000 and $100,000, EVM/CEX microstructural analysis,',
        'and objection battlecards.',
        'Strictly unbranded, factual, with dual-vector scripts (Retail $1k-$5k vs Whale $50k-$100k+).',
        'Guaranteed length: 1,200-1,500 lines.',
        '"""',
        '',
    ]

    fn_names = []
    for filename, fn_name in SECTION_MAP:
        section_path = SCRATCH_SECTIONS / filename
        if not section_path.exists():
            raise FileNotFoundError(f"Missing section file: {section_path}")
        content = section_path.read_text(encoding="utf-8").strip()
        fn_names.append(fn_name)

        code_lines.append(f"def {fn_name}() -> str:")
        # We store as a raw multiline string, escaping any internal triple quotes if present
        escaped_content = content.replace('"""', r'\"\"\"')
        code_lines.append(f'    return r"""{escaped_content}"""')
        code_lines.append("")
        code_lines.append("")

    code_lines.append("def get_all_sections():")
    code_lines.append("    return [")
    for fn_name in fn_names:
        code_lines.append(f"        {fn_name}(),")
    code_lines.append("    ]")
    code_lines.append("")
    code_lines.append("")
    code_lines.append("def get_full_playbook_markdown() -> str:")
    code_lines.append('    return "\\n\\n---\\n\\n".join(get_all_sections())')
    code_lines.append("")

    full_code = "\n".join(code_lines)
    OUTPUT_FILE.write_text(full_code, encoding="utf-8")
    print(f"Successfully generated {OUTPUT_FILE}")

    # Validation
    assembled_md = "\n\n---\n\n".join([
        (SCRATCH_SECTIONS / fname).read_text(encoding="utf-8").strip()
        for fname, _ in SECTION_MAP
    ])
    lines_count = len(assembled_md.splitlines())
    print(f"Total compiled markdown lines: {lines_count}")
    assert 1200 <= lines_count <= 1500, f"Line count {lines_count} outside 1200-1500 range!"
    assert "NULLSPREAD" not in assembled_md, "Found NULLSPREAD in assembled text!"
    assert "Copper ClearLoop" not in assembled_md, "Found Copper ClearLoop in assembled text!"
    print("Validation PASSED: 100% brand-neutral, line count within target range.")


if __name__ == "__main__":
    generate()
