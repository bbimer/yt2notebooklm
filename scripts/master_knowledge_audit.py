# -*- coding: utf-8 -*-
"""
Master audit script for all 7 Knowledge Base files in Obsidian.
"""

import os
import re

DIR_PATH = r"D:\Obsidian\Syndicate Intelligence\Syndicate Intelligence\10_База_знаний"

files = [
    ("📖 День 1 — Словарь терминов и механик рынка.md", "День 1: Словарь и основы"),
    ("📖 День 2 — Архитектура бирж и маркет-мейкинг.md", "День 2: Маркет-мейкинг (M/02)"),
    ("📖 День 3 — Деривативы и дельта-нейтральность.md", "День 3: Деривативы & Базис (M/03)"),
    ("📖 День 4 — Микроструктура биржевого стакана и поток ордеров.md", "День 4: Микроструктура (M/04)"),
    ("📖 День 5 — Блокчейн-инфраструктура и ончейн-логистика.md", "День 5: Ончейн & MEV (M/05)"),
    ("📖 День 6 — Управление рисками, хеджирование и безопасность.md", "День 6: Риск & Хеджирование (M/06)"),
    ("📖 День 7 — Аналитический стек и системное преимущество.md", "День 7: Квант-стек (M/07)")
]

print("=== MASTER KNOWLEDGE BASE AUDIT ===")
print(f"Target Directory: {DIR_PATH}\n")

total_bytes = 0
results = []

for fname, title_label in files:
    fpath = os.path.join(DIR_PATH, fname)
    if not os.path.exists(fpath):
        print(f"ERROR: File missing: {fname}")
        continue
    
    size = os.path.getsize(fpath)
    total_bytes += size
    size_kb = size / 1024
    
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
        
    has_tab = '\t' in content
    has_nullspread = 'NULLSPREAD' in content
    has_unverified = 'UNVERIFIED' in content
    
    # Count cards in Sec VI
    cards_count = len(re.findall(r"(?:### КАРТОЧКА \d+:|#### Боевая карточка \d+:)", content))
    # Count glossary terms in Sec VII (or Day 1)
    if "День 1" in fname:
        terms_count = len(re.findall(r"## (?:Термин \d+:|Инженерный термин)", content))
    else:
        terms_count = len(re.findall(r"^\d+\.\s+\*\*", content, flags=re.MULTILINE))
        
    # Count video dossiers in Sec VIII
    vids_count = len(re.findall(r"(?:#### ДОСЬЕ ВИДЕО:|#### Видео-досье:)", content))
    # Count web dossiers in Sec VIII
    web_count = len(re.findall(r"(?:#### ДОСЬЕ ВЕБ-ДОКУМЕНТА:|#### Веб-досье:|#### Аналитическое досье документа:)", content))
    
    results.append({
        "label": title_label,
        "file": fname,
        "size_kb": size_kb,
        "size_bytes": size,
        "has_tab": has_tab,
        "clean_brand": (not has_nullspread) and (not has_unverified),
        "cards": cards_count,
        "terms": terms_count,
        "videos": vids_count,
        "web": web_count
    })

print(f"{'Модуль / Том':<35} | {'Размер':<10} | {'Табы':<5} | {'Бренд':<6} | {'Карточки':<8} | {'Глоссарий':<9} | {'Источники (Видео / Веб)'}")
print("-" * 115)
for r in results:
    tab_str = "ERR" if r['has_tab'] else "OK"
    brand_str = "OK" if r['clean_brand'] else "ERR"
    cards_str = f"{r['cards']}/10" if r['cards'] else "N/A"
    terms_str = f"{r['terms']} шт" if r['terms'] else "N/A"
    sources_str = f"{r['videos']} видео / {r['web']} веб" if (r['videos'] or r['web']) else "N/A"
    print(f"{r['label']:<35} | {r['size_kb']:>6.1f} KB | {tab_str:<5} | {brand_str:<6} | {cards_str:<8} | {terms_str:<9} | {sources_str}")

print("-" * 115)
print(f"ИТОГО: 7 томов | Общий объем: {total_bytes / 1024:.1f} KB ({total_bytes / (1024*1024):.2f} MB)")
