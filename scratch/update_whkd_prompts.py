from pathlib import Path

hotkey_lines = """
# Alt + Ctrl + S: Скопировать чистый промпт Executive Summary (для прикрепленного файла)
alt + ctrl + s          : powershell -NoProfile -NonInteractive -WindowStyle Hidden -Command "cd C:\\Users\\root\\Desktop\\_Intelligence\\nullspread-research-academy; python -m research_academy.cli prompt summary"

# Alt + Ctrl + A: Скопировать чистый промпт жесткого аудита (для прикрепленного файла)
alt + ctrl + a          : powershell -NoProfile -NonInteractive -WindowStyle Hidden -Command "cd C:\\Users\\root\\Desktop\\_Intelligence\\nullspread-research-academy; python -m research_academy.cli prompt audit"

# Alt + Ctrl + C: Скопировать мульти-промпт кросс-анализа и синтеза (для пачки из 2+ файлов)
alt + ctrl + c          : powershell -NoProfile -NonInteractive -WindowStyle Hidden -Command "cd C:\\Users\\root\\Desktop\\_Intelligence\\nullspread-research-academy; python -m research_academy.cli prompt compare"
"""

for path_str in [
    r"C:\Users\root\.config\whkdrc",
    r"C:\Users\root\Desktop\_customization\whkd\whkdrc",
]:
    p = Path(path_str)
    if p.exists():
        content = p.read_text(encoding="utf-8").rstrip()
        if "alt + ctrl + s" not in content:
            new_content = content + "\n" + hotkey_lines + "\n"
            p.write_text(new_content, encoding="utf-8", newline="\n")
            print(f"Updated {p}")
        else:
            print(f"Already present in {p}")

