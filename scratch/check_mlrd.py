import fitz

doc = fitz.open(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\Day_1_Sales_Playbook.pdf")
pages_to_check = [16, 17, 22, 34]

for p in pages_to_check:
    print(f"=== PAGE {p} ===")
    lines = doc[p-1].get_text().splitlines()
    for l in lines:
        if "млрд" in l or ".3" in l or ".4" in l:
            print("  ", l)

