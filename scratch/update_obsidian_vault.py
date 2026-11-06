import os
import shutil
from pathlib import Path

SRC_PACK = Path(r"C:\Users\root\Desktop\_Intelligence\nullspread-research-academy\exports\notebooklm_pack")
VAULT = Path(r"D:\Obsidian\Syndicate Intelligence\Syndicate Intelligence")

BACKUP_DIR = VAULT / ".backup_pre_update_20261031"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

print(f"Source pack: {SRC_PACK}")
print(f"Vault root: {VAULT}")
print(f"Backup dir: {BACKUP_DIR}")

# 1. Backup existing files
files_to_backup = [
    VAULT / "20_Практика_и_Кейсы" / "M01_Analytical_Playbook.md",
    VAULT / "10_База_знаний" / "📖 День 1 - Словарь терминов и механик рынка.md",
    VAULT / "30_Материалы" / "M01_Prompt_Builder.md",
    VAULT / "🧭 Syndicate Intelligence - Главный пульт.md",
]

for f in files_to_backup:
    if f.exists():
        rel = f.relative_to(VAULT)
        dest = BACKUP_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        print(f"[BACKUP] {rel} -> {dest}")

# 2. Update 20_Практика_и_Кейсы/M01_Analytical_Playbook.md with full Day_1_Sales_Playbook.md
sales_playbook_src = SRC_PACK / "Day_1_Sales_Playbook.md"
sales_content = sales_playbook_src.read_text(encoding="utf-8")

playbook_frontmatter = """---
title: M01 - Корпоративный учебник и плейбук продаж
module: M/01
created: 2026-10-27
updated: 2026-10-31
tags:
  - playbook
  - sales-playbook
  - case-studies
  - sales-objections
  - compliance
  - microstructure
---

[[🧭 Syndicate Intelligence - Главный пульт|Главный пульт]] / [[20_Практика_и_Кейсы/M01_Fast_Track_Closer|Тактический клоузер]] / [[20_Практика_и_Кейсы/M01_Battlecard|Батлкарта звонка]]

"""

dest_playbook = VAULT / "20_Практика_и_Кейсы" / "M01_Analytical_Playbook.md"
dest_playbook.write_text(playbook_frontmatter + sales_content, encoding="utf-8")
print(f"[UPDATED] {dest_playbook} ({dest_playbook.stat().st_size} bytes)")

# 3. Add 20_Практика_и_Кейсы/M01_Fast_Track_Closer.md
closer_src = SRC_PACK / "Fast_Track_Closer_Playbook.md"
closer_content = closer_src.read_text(encoding="utf-8")

closer_frontmatter = """---
title: M01 - Тактический плейбук клоузера (Telegram)
module: M/01
created: 2026-10-30
updated: 2026-10-31
tags:
  - closer
  - telegram
  - sales-scripts
  - fast-track
---

[[🧭 Syndicate Intelligence - Главный пульт|Главный пульт]] / [[20_Практика_и_Кейсы/M01_Analytical_Playbook|Полный плейбук продаж]] / [[20_Практика_и_Кейсы/M01_Battlecard|Батлкарта звонка]]

"""

dest_closer = VAULT / "20_Практика_и_Кейсы" / "M01_Fast_Track_Closer.md"
dest_closer.write_text(closer_frontmatter + closer_content, encoding="utf-8")
print(f"[CREATED] {dest_closer} ({dest_closer.stat().st_size} bytes)")

# 4. Add 20_Практика_и_Кейсы/M01_Battlecard.md
battlecard_src = SRC_PACK / "Day_1_BATTLECARD.md"
battlecard_content = battlecard_src.read_text(encoding="utf-8")

battlecard_frontmatter = """---
title: M01 - Батлкарта возражений и формул
module: M/01
created: 2026-10-29
updated: 2026-10-31
tags:
  - battlecard
  - cheatsheet
  - sales-objections
  - quick-reference
---

[[🧭 Syndicate Intelligence - Главный пульт|Главный пульт]] / [[20_Практика_и_Кейсы/M01_Analytical_Playbook|Полный плейбук]] / [[20_Практика_и_Кейсы/M01_Fast_Track_Closer|Тактический клоузер]]

"""

dest_battlecard = VAULT / "20_Практика_и_Кейсы" / "M01_Battlecard.md"
dest_battlecard.write_text(battlecard_frontmatter + battlecard_content, encoding="utf-8")
print(f"[CREATED] {dest_battlecard} ({dest_battlecard.stat().st_size} bytes)")

# 5. Add Day 2 and Day 3 knowledge base materials
day2_src = SRC_PACK / "Day_2_01_Market_Structure.md"
if day2_src.exists():
    d2_content = day2_src.read_text(encoding="utf-8")
    d2_frontmatter = """---
title: День 2 - Архитектура бирж, AMM-пулы и алгоритмы маркет-мейкеров
module: M/02
created: 2026-10-28
updated: 2026-10-31
tags:
  - day2
  - market-structure
  - amm
  - orderbook
  - market-making
---

[[🧭 Syndicate Intelligence - Главный пульт|Главный пульт]] / [[10_База_знаний|База знаний]]

"""
    dest_d2 = VAULT / "10_База_знаний" / "📖 День 2 - Архитектура бирж и маркет-мейкинг.md"
    dest_d2.write_text(d2_frontmatter + d2_content, encoding="utf-8")
    print(f"[CREATED] {dest_d2} ({dest_d2.stat().st_size} bytes)")

day3_src = SRC_PACK / "Day_3_02_Arbitrage_and_Derivatives.md"
if day3_src.exists():
    d3_content = day3_src.read_text(encoding="utf-8")
    d3_frontmatter = """---
title: День 3 - Деривативы, механика фандинга и дельта-нейтральный арбитраж
module: M/03
created: 2026-10-28
updated: 2026-10-31
tags:
  - day3
  - derivatives
  - funding-rate
  - delta-neutral
  - basis-trading
---

[[🧭 Syndicate Intelligence - Главный пульт|Главный пульт]] / [[10_База_знаний|База знаний]]

"""
    dest_d3 = VAULT / "10_База_знаний" / "📖 День 3 - Деривативы и дельта-нейтральность.md"
    dest_d3.write_text(d3_frontmatter + d3_content, encoding="utf-8")
    print(f"[CREATED] {dest_d3} ({dest_d3.stat().st_size} bytes)")

# 6. Add 30_Материалы/M01_Telegram_Closer_Simulator.md
sim_src = SRC_PACK / "Fast_Track_Exam_Simulator.md"
if sim_src.exists():
    sim_content = sim_src.read_text(encoding="utf-8")
    sim_frontmatter = """---
title: M01 - Интерактивный симулятор экзаменатора клоузера
module: M/01
created: 2026-10-30
updated: 2026-10-31
tags:
  - exam-simulator
  - telegram
  - closer
  - prompt
---

[[🧭 Syndicate Intelligence - Главный пульт|Главный пульт]] / [[20_Практика_и_Кейсы/M01_Fast_Track_Closer|Тактический клоузер]]

"""
    dest_sim = VAULT / "30_Материалы" / "M01_Telegram_Closer_Simulator.md"
    dest_sim.write_text(sim_frontmatter + sim_content, encoding="utf-8")
    print(f"[CREATED] {dest_sim} ({dest_sim.stat().st_size} bytes)")

# 7. Copy PDF files into 30_Материалы
pdf_files = [
    "Day_1_Sales_Playbook.pdf",
    "Fast_Track_Closer_Playbook.pdf",
    "Day_1_Battlecard.pdf",
]

for pdf in pdf_files:
    psrc = SRC_PACK / pdf
    if psrc.exists():
        pdest = VAULT / "30_Материалы" / pdf
        shutil.copy2(psrc, pdest)
        print(f"[COPIED PDF] {pdf} -> {pdest} ({pdest.stat().st_size} bytes)")

# 8. Update 🧭 Syndicate Intelligence - Главный пульт.md
dashboard_content = """---
tags:
  - moc
  - dashboard
  - syndicate
updated: 2026-10-31
---

> Центральный узел управления базой знаний и пониманием рынка.  
> 📜 [[00_Регламент_и_Программа|00. Регламент и программа деска Intelligence]]  
> ⚡ [[00_Методология_спидрана_программы|00. Методология спидрана: от базы до звонка за 90 минут]]

---

## 📱 Быстрый доступ для PocketBook / Mobile (PDF для ридера)
- [[30_Материалы/Day_1_Sales_Playbook.pdf|📄 Day 1 Sales Playbook (Полный учебник, 5 слоев)]]
- [[30_Материалы/Fast_Track_Closer_Playbook.pdf|📄 Fast Track Closer Playbook (Тактический клоузер Telegram)]]
- [[30_Материалы/Day_1_Battlecard.pdf|📄 Day 1 Battlecard (Батлкарта для звонков на 1 экран)]]

---

## ⚡ 1. Трекер спринта (Roadmap освоения по дням)

- [x] **День 1: Фундамент активов, VC-токеномика и базовая микроструктура**
  - **Словарь:** [[10_База_знаний/📖 День 1 - Словарь терминов и механик рынка|📖 День 1 - Словарь терминов и механик рынка]] (27 механик под капотом).
  - **Полный плейбук:** [[20_Практика_и_Кейсы/M01_Analytical_Playbook|M01 - Корпоративный учебник и плейбук продаж]] (10 разделов по 5 обязательным слоям: Метафора + Кейс Минюста/ФБР + Unit-экономика $10k/$100k + Технический пруф + Скрипты Вектор А/Б).
  - **Тактический клоузер:** [[20_Практика_и_Кейсы/M01_Fast_Track_Closer|M01 - Тактический плейбук клоузера]] (скрипты переписки, тест на $20, перевод на $1,000–$2,000).
  - **Батлкарта звонка:** [[20_Практика_и_Кейсы/M01_Battlecard|M01 - Батлкарта возражений и формул]] (шпаргалка для звонка, формулы, комплаенс).
  - **Аттестация:** [[30_Материалы/M01_Prompt_Builder|M01 - Промпт-аттестатор (Академический)]] | [[30_Материалы/M01_Telegram_Closer_Simulator|M01 - Симулятор Telegram (Трейдер Артём, 5 раундов)]].

- [x] **День 2: Архитектура бирж (CEX vs DEX), AMM-пулы и алгоритмы маркет-мейкеров**
  - **База знаний:** [[10_База_знаний/📖 День 2 - Архитектура бирж и маркет-мейкинг|📖 День 2 - Архитектура бирж и маркет-мейкинг]]
  - Фокус: фрагментация ликвидности, формулы AMM ($x \\cdot y = k$), механика пулов, работа Wintermute/Jump, арбитраж спредов.

- [x] **День 3: Деривативы, механика фандинга и дельта-нейтральный арбитраж**
  - **База знаний:** [[10_База_знаний/📖 День 3 - Деривативы и дельта-нейтральность|📖 День 3 - Деривативы и дельта-нейтральность]]
  - Фокус: бессрочные фьючерсы (Perps), спот vs фьюч, ставка финансирования, хеджирование, базис, каскады ликвидаций.

- [ ] **День 4: Микроструктура биржевого стакана и поток ордеров**
  - Фокус: Matching Engine, стакан L2/L3, Maker/Taker комиссии, проскальзывание (Slippage), айсберги, детекция Wash Trading.

- [ ] **День 5: Блокчейн-инфраструктура и ончейн-логистика**
  - Фокус: финальность транзакций, L1 vs L2 (газ и задержки), чтение смарт-контрактов в Etherscan, горячие/холодные кошельки бирж.

- [ ] **День 6: Управление рисками, хеджирование и безопасность**
  - Фокус: риски исполнения (Latency/Execution risk), AML/KYT комплаенс и блокировки, риск контрагента, скам-биржи и заморозки вывода.

- [ ] **День 7: Аналитический стек, спреды и системное преимущество (Edge)**
  - Фокус: спред-графики, работа скринеров по API, почему сигнальные каналы ведут к сливу (математика EV), формирование Edge.

---

## 📚 2. База знаний: День 1 (Все 27 терминов в одном файле)
*Файл: [[10_База_знаний/📖 День 1 - Словарь терминов и механик рынка|📖 День 1 - Словарь терминов и механик рынка]]*

* [[10_База_знаний/📖 День 1 - Словарь терминов и механик рынка#Блок 1: Архитектура активов и Стейблкоины|Блок 1: Архитектура активов и Стейблкоины (1–8)]] *(Coin, Token, Stablecoin, Issuer, Reserves, Minting, Depeg, Bank Run)*
* [[10_База_знаний/📖 День 1 - Словарь терминов и механик рынка#Блок 2: Токеномика и Венчурные механики (VC)|Блок 2: Токеномика и Венчурные механики (VC) (9–17)]] *(Market Cap, FDV, Low Float, Vesting, Cliff, Unlocks, Staking, Staking Loophole, OTC)*
* [[10_База_знаний/📖 День 1 - Словарь терминов и механик рынка#Блок 3: Микроструктура рынка и Манипуляции|Блок 3: Микроструктура рынка и Манипуляции (18–24)]] *(Microstructure, Retail, Smart Money, HFT, Wash Trading, Iceberg, Overflow Test)*
* [[10_База_знаний/📖 День 1 - Словарь терминов и механик рынка#Блок 4: Институциональный подход и Защита|Блок 4: Институциональный подход и Защита (25–27)]] *(Delta-Neutral, Funding Rate, Negative EV)*
"""

dest_dashboard = VAULT / "🧭 Syndicate Intelligence - Главный пульт.md"
dest_dashboard.write_text(dashboard_content, encoding="utf-8")
print(f"[UPDATED] {dest_dashboard} ({dest_dashboard.stat().st_size} bytes)")

print("\n--- ALL VAULT UPDATES COMPLETED SUCCESSFULLY ---")

