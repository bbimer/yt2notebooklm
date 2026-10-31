"""Curriculum Synthesizer: Merges Web Ground Truth (Hard Spec) and YouTube Field Intel into Sales Playbooks and Battlecards.
Unbranded, universal institutional weapon with zero fact loss and dual-ticket targeting ($1k vs $100k).
Section-by-section generation architecture guaranteeing 1,200-1,500 lines of rigorous Markdown.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, List

from research_academy.pipeline.playbook_renderer import PlaybookRenderer


class CurriculumSynthesizer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.exports_dir = project_root / "exports" / "notebooklm_pack"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.renderer = PlaybookRenderer()

    def synthesize_day_1_pack(self) -> Dict[str, Path]:
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

    def synthesize_fast_track_closer_pack(self) -> Dict[str, Path]:
        """
        Synthesizes the lightweight Fast-Track Closer Pack for retail street closers ($1k-$5k):
        1. Fast_Track_Closer_Playbook.md -> Fast_Track_Closer_Playbook.pdf
        2. Fast_Track_Exam_Simulator.md (Telegram Closer Simulator prompt)
        """
        from research_academy.pipeline.closer_fast_track import (
            get_fast_track_closer_playbook_markdown,
            get_fast_track_exam_simulator_markdown,
        )

        closer_md = get_fast_track_closer_playbook_markdown()
        closer_md_path = self.exports_dir / "Fast_Track_Closer_Playbook.md"
        closer_md_path.write_text(closer_md, encoding="utf-8")

        exam_md = get_fast_track_exam_simulator_markdown()
        exam_md_path = self.exports_dir / "Fast_Track_Exam_Simulator.md"
        exam_md_path.write_text(exam_md, encoding="utf-8")

        closer_pdf = self.renderer.render_pdf(
            markdown_path=closer_md_path,
            output_pdf_path=self.exports_dir / "Fast_Track_Closer_Playbook.pdf",
            title="Боевой плейбук клоузера: от $20 до $2,000+",
            subtitle="Практическое руководство по закрытию розничных лидов в Telegram и на созвонах",
            is_battlecard=False,
        )

        return {
            "closer_playbook_md": closer_md_path,
            "closer_playbook_pdf": closer_pdf,
            "exam_simulator_md": exam_md_path,
        }

    def _build_day_1_battlecard(self) -> str:
        return r"""# ДЕНЬ 1. БОЕВАЯ ШПАРГАЛКА СЕЙЛЗА (BATTLECARD A4)

> ВНИМАНИЕ: **Главное правило звонка:** Не спорь с клиентом о его монетах и не пытайся угадать курс. Покажи, что открытый рынок математически устроен как машина по отъему ликвидности у ритейла, а системная прибыль извлекается только через дельта-нейтральный арбитраж (Δ = 0).

---

## 3 КИЛЛЕР-ФАКТА С ЦИФРАМИ ДЛЯ ПЕРЕХВАТА АВТОРИТЕТА

1. **8 против 1:** В цикле 2024–2025 средний Float / FDV = **12.3%** (Delphi Digital). На каждый $1 торгуемой ликвидности приходится $8 залоченного навеса. До 2030 года выходит **$155 млрд** разлоков против $80 млрд спроса. Альткоины гарантированно размываются на 40–70% в год.
2. **0.15% защиты:** Фонды не могут захеджировать разлоки шортом — нет открытого интереса (OI). У ICP при локе в $110 млрд весь биржевой OI был $170 млн (**0.15% покрытия**). Падение неизбежно. «Бычьи анлоки» (рост AXS на +19%, APE на +40%) — это не покупки, а принудительный unwind шортов на отрицательном фандинге.
3. **96.4% картеля:** При волатильности от 2% три HFT-билдера (Manta, Rsync, BeaverBuild) забирают **96.4% блоков Ethereum** (arXiv:2305.19150). Внебиржевые маркет-мейкеры рисуют 98% объемов (дело ФБР против Gotbit по статье Wire Fraud).

---

## МАТРИЦА БЫСТРОГО РЕАГИРОВАНИЯ (ЧТО СКАЗАТЬ НА ЗВОНКЕ)

| Если клиент говорит (Триггер) | Какую метафору и цифру дать в ответ (Контрудар) | Мост в продукт (Логика закрытия на арбитраж) |
| :--- | :--- | :--- |
| **«У проекта есть официальный аудит, смарт-контракт безопасен»** | «Аудит проверяет код, а не честность. В EIP-20 decimals опциональны, а approve имеет уязвимость гонки состояний. 99% скамов имели аудит». | «Мы не покупаем токены на веру. Системный доход дает межбиржевой спред, где риск чужого смарт-контракта равен нулю». |
| **«Скоро разлок, на прошлом разлоке монета выросла на 20%!»** | «Это "бычий анлок" (как у AXS +19% и APE +40%) — не спрос толпы, а инсайдеры откупают свои шорты, чтобы не платить отрицательный фандинг. Затем обвал на 90% (Mantra -92%)». | «Пока ритейл ловят на ложном пампе, арбитражер забирает ставку финансирования (Funding Rate) с паникующих медведей». |
| **«USDC регулируется США, депег невозможен»** | «В марте 2023 у Circle зависло $3.3 млрд в SVB, и USDC упал до $0.87. Шлюз выкупа от $100k, а в Curve 3pool при перекосе > 85% проскальзывание улетает до 25% через get_dy». | «Алгоритмический риск-менеджмент мониторит инвариант Curve в реальном времени, автоматически выходя из ноги до обрыва ликвидности». |
| **«Я застейкаю под 25% APR и буду жить на проценты»** | «Polychain вложила $20M в Celestia, стейкала залоченные токены и забрала $80M кэша до клифа. В Aptos инсайдеры держат 97% стейка, а в LooksRare вынули $38M, размыв вас в ноль». | «Вместо номинальных фантиков, падающих на 60%, профессиональный капитал забирает чистую долларовую доходность 20–35% годовых». |
| **«Фонды не могут слить — у них юридический лок SAFT»** | «Фонды продают SAFT на tZERO со скидкой 40–70% и шортят деривативы. Они в кэше сегодня, а покупатель выльет всё в рынок в день разлока». | «Институционалы хеджируют риски на опережение. Мы используем те же дельта-нейтральные механики для стабильного профита». |

---

## 3 ТИПАЖА КЛИЕНТОВ И РАЗБОР КАВЕРЗНЫХ ВБРОСОВ

### Типаж 1: «Инженер-разработчик» (давит на смарт-контракты и код)
* *Вброс:* «Вы говорите, что EIP-20 дырявый. Но OpenZeppelin давно использует SafeERC20 и increaseAllowance. В чем проблема?»
* *Эталонный ответ сейлза:* «OpenZeppelin защищает контракт от ошибки компиляции, но не защищает от Silent Failure, когда токен возвращает false вместо revert или имеет нестандартные хуки комиссии (fee-on-transfer). Если алгоритм ждет 1000 токенов, а получает 950 из-за скрытого налога, дельта-нога ломается. Профессиональный арбитраж использует симуляцию транзакций до отправки в сеть».

### Типаж 2: «Бывалый трейдер Bybit» (торгует фьючерсы, понимает стакан и фандинг)
* *Вброс:* «Если фандинг станет отрицательным, ваша дельта-нейтральная стратегия начнет жрать депозит. Как вы выживаете?»
* *Эталонный ответ сейлза:* «Отрицательный фандинг — это признак паники шортистов, когда расширяется межплощадочный базис. Мы не сидим в пассивной позе: алгоритм либо разворачивает синтетическую ногу (лонг фьючерс + шорт спот), собирая комиссию с медведей, либо ребалансирует объем на биржу с положительным базисом. Вы платите фандинг, а мы его собираем».

### Типаж 3: «Жертва разлока» (обожглась на Celestia/Mantra, боится заходить в крипту)
* *Вброс:* «Я уже потерял $30,000 на TIA и WLFI. Все криптопроекты — это скам и разгрузка фондов».
* *Эталонный ответ сейлза:* «Вы абсолютно правы: 95% проектов создаются венчуром как фабрики по генерации exit liquidity. В октябре 2024 года ФБР в операции Token Mirrors доказало, что 98% объемов маркет-мейкеров Gotbit и CLS Global — это фиктивный wash-trading. Разница в том, что мы не покупаем эти монеты. Мы зарабатываем на спреде между биржами в момент паники, а баланс всегда держим в твердом долларе».

---

## СТОП-СЛОВА ДЛЯ МЕНЕДЖЕРА (ЧТО КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО ГОВОРИТЬ)
* Запрещено: *«Это абсолютно безрисковая стратегия»* -> **Говорим:** «Стратегия дельта-нейтральна к цене монеты, рыночный риск исключен, риск сведен к инфраструктурному базису».
* Запрещено: *«Мы гарантируем 30% в месяц»* -> **Говорим:** «Историческая доходность математического арбитража составляет 20–35% годовых в долларе без направленных ставок».
* Запрещено: *«Эта монета скоро рухнет»* -> **Говорим:** «Математический навес предложения по данным Delphi Digital превышает емкость стакана в 8 раз».
"""

    def _build_day_1_playbook(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_full_playbook_markdown()

    def _build_playbook_intro(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_intro_enriched()

    def _build_playbook_sec1(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_sec1_enriched()

    def _build_playbook_sec2(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_sec2_enriched()

    def _build_playbook_sec3(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_sec3_enriched()

    def _build_playbook_sec4(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_sec4_enriched()

    def _build_playbook_sec5(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_sec5_enriched()

    def _build_playbook_sec6(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_sec6_enriched()

    def _build_playbook_glossary(self) -> str:
        from src.research_academy.pipeline import playbook_content
        return playbook_content.get_glossary_enriched()

    def _build_day_1_notebooklm(self) -> str:
        return r"""# ДЕНЬ 1. КОНСПЕКТ ДЛЯ АУДИО-ПОДКАСТА NOTEBOOKLM
## Модуль M/01: Токеномика, депег стейблкоинов и архитектура L1

### Ключевые тезисы выпуска:
1. **Почему аудит смарт-контракта не защищает от потери денег:** Анатомия стандарта ERC-20, гонка состояний Approve Race Condition (\$100 -> \$50 = \$150), опциональность полей decimals/name/symbol, опасность Silent Failure без вызова revert. Unit-экономика потерь розничного трейдера (-3.2% на входе, -11.5% на крупном ордере).
2. **Как устроен мемпул и почему ритейл всегда опаздывает:** Формула базовой комиссии EIP-1559, лимит роста на 12.5% за блок (+224% за 10 блоков, в 10.5 раз за 20 блоков), монополия PBS (Proposer-Builder Separation), где 3 HFT-билдера (Manta, Rsync, BeaverBuild) контролируют 96.4% доходных блоков за счет приватного потока ордеров (arXiv:2305.19150). Формула потерь LVR и кубический закон времени блока.
3. **Физика депега стейблкоинов и оракульное заражение:** Банкротство SVB (\$3.3 млрд у Circle), падение USDC до \$0.87, ловушка банковских выходных и шлюзы выкупа от \$100,000. Инвариант Curve StableSwap, обрыв ликвидности при перекосе пула свыше 85%, искажение оракулов get_dy / get_virtual_price и мгновенный экспорт депега на L2 через протокол CCTP.
4. **Хищная токеномика Low Float / High FDV:** Исследование Delphi Digital (средний Float/FDV 2024 года = 12.3%), навес разлоков в \$155 млрд до 2030 года против \$80 млрд спроса. Невозможность деривативного хеджирования (ICP: 0.15% покрытия, OXY: 0.36%). Механика «бычьих анлоков» (AXS +19%, APE +40%) как принудительный unwind шортов на отрицательном фандинге. Крах Mantra (OM) на -92% и пирамида WLFI.
5. **Стейкинг-лазейка и спецоперация ФБР:** Схема The Insider Re-Lock: вывод \$38.04 млн инсайдерами LooksRare, 97% концентрация стейка у инсайдеров Aptos, кейс Polychain Capital (\$80 млн кэша со стейкинг-наград Celestia до клиффа). Вторичный рынок SAFT на tZERO со скидкой 40–70%. Спецоперация ФБР Token Mirrors против Gotbit и CLS Global по уголовной статье Wire Fraud.
6. **Вывод:** Направленный трейдинг розничных участников математически обречен ($\mathbb{E} < 0$). Устойчивый доход формируется исключительно через дельта-нейтральный арбитраж ($\Delta = 0$) и сбор межбиржевого базиса.
"""


if __name__ == "__main__":
    synthesizer = CurriculumSynthesizer(Path(__file__).resolve().parent.parent.parent.parent)
    res = synthesizer.synthesize_day_1_pack()
    for k, v in res.items():
        print(f"{k}: {v} (size={v.stat().st_size} bytes)")
