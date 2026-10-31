import shutil
from pathlib import Path

# Clean computer_science from exports/notebooklm_pack
cs_dir = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\computer_science")
if cs_dir.exists():
    shutil.rmtree(cs_dir)
    print("Removed exports/notebooklm_pack/computer_science")

# Add cleanup in test_isomorphic_pipeline.py
test_file = Path(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\tests\test_isomorphic_pipeline.py")
test_text = test_file.read_text(encoding="utf-8")
old_part = '    res_export = runner.invoke(cli, ["export", "--format", "pack", "--domain", "computer_science"])\n    assert res_export.exit_code == 0\n    assert "computer_science" in res_export.output'
new_part = '    res_export = runner.invoke(cli, ["export", "--format", "pack", "--domain", "computer_science"])\n    assert res_export.exit_code == 0\n    assert "computer_science" in res_export.output\n    import shutil\n    shutil.rmtree(Path("exports/notebooklm_pack/computer_science"), ignore_errors=True)'

if old_part in test_text:
    test_text = test_text.replace(old_part, new_part)
    test_file.write_text(test_text, encoding="utf-8")
    print("Updated test_isomorphic_pipeline.py to clean up after test")

