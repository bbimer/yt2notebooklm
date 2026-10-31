import os

pack = r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack"
for f in os.listdir(pack):
    if f.endswith(".md"):
        p = os.path.join(pack, f)
        print(f"{f}: {os.path.getsize(p)} bytes")

