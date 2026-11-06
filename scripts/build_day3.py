# -*- coding: utf-8 -*-
"""
Master compiler for Day 3.
Combines Part A (Master Playbook) and Part B (Source Dossiers) into a single institutional volume.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.append(r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy")

from scripts.day3_part_a import DAY3_PART_A
from scripts.day3_part_b import generate_day3_part_b

DB_PATH = r"c:\Users\root\Desktop\_Intelligence\nullspread-research-academy\data\research_academy.db"
OUTPUT_FILE = r"D:\Obsidian\Syndicate Intelligence\Syndicate Intelligence\10_База_знаний\📖 День 3 — Деривативы и дельта-нейтральность.md"

def main():
    print("Generating Day 3 Part B (Source Dossiers)...")
    part_b = generate_day3_part_b(DB_PATH)
    
    full_content = DAY3_PART_A.strip() + "\n\n" + part_b.strip() + "\n"
    
    # Write to Obsidian Knowledge Base
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_content)
        
    size_bytes = os.path.getsize(OUTPUT_FILE)
    size_kb = size_bytes / 1024
    lines_count = len(full_content.splitlines())
    
    print(f"SUCCESS! Day 3 generated:")
    print(f"  Path: {OUTPUT_FILE}")
    print(f"  Size: {size_bytes} bytes ({size_kb:.2f} KB)")
    print(f"  Lines: {lines_count}")

if __name__ == "__main__":
    main()

