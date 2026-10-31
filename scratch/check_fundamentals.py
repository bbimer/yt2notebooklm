p = r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack\Day_1_00_Fundamentals.md"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

print("Size:", len(text))
print("Has 375:", "375" in text)
print("Has bad_21k:", "2121,000" in text)
print("First 500 chars:")
print(text[:500])

