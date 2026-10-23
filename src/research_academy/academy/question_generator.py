"""Sales Academy Question Generator based on verified knowledge base concepts across all 6 modules."""

from __future__ import annotations

import random
from typing import Dict, List, Optional
from research_academy.database import Database
from research_academy.models import AcademyQuestion, QuestionCategory

TOPIC_ALIASES: Dict[str, str] = {
    "funding-rate-arbitrage": "02_arbitrage_and_derivatives",
    "market-microstructure": "03_orderbook_mechanics",
    "cross-exchange-arbitrage": "02_arbitrage_and_derivatives",
    "onchain-dex-liquidity": "04_onchain_logistics",
    "02_arbitrage_types": "02_arbitrage_and_derivatives",
    "crypto-fundamentals": "00_crypto_fundamentals",
}

CURATED_QUESTIONS: List[AcademyQuestion] = [
    # Модуль 0: Фундамент крипты, блокчейн и токеномика
    AcademyQuestion(
        id="Q-00-FUN-001",
        topic_id="00_crypto_fundamentals",
        category=QuestionCategory.BASIC,
        question="Как устроено обеспечение стейблкоинов USDT и USDC, и почему при высокой волатильности на DEX может временно возникать депег (отклонение от $1)?",
        ideal_answer_key_points=[
            "Эмитенты держат казначейские векселя и фиатные резервы, гарантируя погашение 1:1 крупным институционалам.",
            "На DEX курс определяется балансом пула ликвидности AMM (x*y=k), а не резервами эмитента напрямую.",
            "При панических распродажах арбитражерам нужно время и ликвидность на ончейн-выкуп, из-за чего курс на пуле может кратковременно отклоняться.",
        ],
        forbidden_phrasings=["Стейблкоины никогда не могут отклоняться от $1 ни на цент"],
        source_reference="Module 00: Crypto Fundamentals",
    ),

    # Модуль 1: Архитектура рынка, биржи и маркет-мейкеры
    AcademyQuestion(
        id="Q-01-MKT-001",
        topic_id="01_market_structure",
        category=QuestionCategory.TECHNICAL,
        question="Откуда берется фрагментация ликвидности в крипте и почему на разных биржах и нодах возникают устойчивые перекосы цен (например, Kimchi Premium)?",
        ideal_answer_key_points=[
            "Разные биржи имеют изолированные пулы ликвидности и разные региональные фиатные шлюзы.",
            "Премии (как Kimchi) возникают из-за валютного контроля и ограничений на трансграничный вывод капитала.",
            "Маркет-мейкеры балансируют цены, но скорость выравнивания ограничена скоростью ончейн-переводов и лимитами риска.",
        ],
        forbidden_phrasings=["Все цены на всех биржах выравниваются за секунду"],
        source_reference="Module 01: Market Architecture",
    ),

    # Модуль 2: Эволюция и виды криптоарбитража
    AcademyQuestion(
        id="Q-02-ARB-001",
        topic_id="02_arbitrage_types",
        category=QuestionCategory.TECHNICAL,
        question="Объясните механику спот-фьючерсного базиса (cash-and-carry trade): как устраняется ценовой риск актива при удержании позиции?",
        ideal_answer_key_points=[
            "Одновременное открытие длинной позиции на споте и короткой позиции на бессрочном фьючерсе в равном объеме.",
            "Дельта портфеля равна нулю (рост цены компенсируется прибылью на споте, падение — прибылью на фьючерсе).",
            "Доход формируется за счет получения ставки финансирования (funding rate), выплачиваемой покупателями продавцам.",
        ],
        forbidden_phrasings=[
            "Это абсолютно безрисковая стратегия",
            "Гарантированная прибыль 100%",
        ],
        source_reference="CLAIM-002",
    ),
    AcademyQuestion(
        id="Q-02-ARB-002",
        topic_id="02_arbitrage_types",
        category=QuestionCategory.SKEPTICAL_CLIENT,
        question="Клиент говорит: «Крупные HFT-маркетмейкеры вроде Wintermute или Jump забирают весь спред за микросекунды. Зачем мне вы?» Что вы ответите?",
        ideal_answer_key_points=[
            "HFT забирают микросекундные ценовые неэффективности на топовых высоколиквидных парах.",
            "Фандинг-арбитраж — это структурная позиционная сделка, удерживаемая часами и днями, а не HFT-спред.",
            "Емкость сделок на парах средней ликвидности ($50k-$200k) слишком мала для институциональных миллиардных фондов, но оптимальна для частных десков.",
        ],
        forbidden_phrasings=[
            "Наш бот быстрее Wintermute",
            "Мы используем секретный искусственный интеллект, обгоняющий всех",
        ],
        source_reference="OBJ-001",
    ),
    AcademyQuestion(
        id="Q-02-ARB-003",
        topic_id="02_arbitrage_types",
        category=QuestionCategory.UNCERTAINTY,
        question="Клиент спрашивает: «Какую точную доходность (APY) вы гарантируете в следующем месяце?»",
        ideal_answer_key_points=[
            "Четкое признание рыночной неопределенности: фиксированная доходность не гарантируется.",
            "Ставка финансирования является плавающей и зависит от рыночных настроений и волатильности.",
            "Объяснение исторических диапазонов с обязательным указанием, что прошлая доходность не гарантирует будущую.",
        ],
        forbidden_phrasings=[
            "Мы гарантируем от 30% годовых",
            "Вы точно не потеряете ни цента",
        ],
        source_reference="CLAIM-003",
    ),

    # Модуль 3: Микроструктура биржевого стакана
    AcademyQuestion(
        id="Q-03-OB-001",
        topic_id="03_orderbook_mechanics",
        category=QuestionCategory.BASIC,
        question="В чем разница между исполнением ордера по типу Maker и Taker, и как проскальзывание (slippage) влияет на издержки арбитража?",
        ideal_answer_key_points=[
            "Maker предоставляет ликвидность в стакан лимитным ордером (получает рибейт или платит меньшую комиссию).",
            "Taker забирает ликвидность рыночным ордером (платит повышенную комиссию и рискует нарваться на проскальзывание).",
            "При межбиржевом арбитраже комиссии тейкера и проскальзывание в тонком стакане могут полностью уничтожить спред.",
        ],
        forbidden_phrasings=["Проскальзывание не имеет значения"],
        source_reference="Module 03: Orderbook Mechanics",
    ),

    # Модуль 4: Блокчейн-инфраструктура и ончейн-логистика
    AcademyQuestion(
        id="Q-04-ONCHAIN-001",
        topic_id="04_onchain_logistics",
        category=QuestionCategory.TECHNICAL,
        question="Что такое финальность транзакции (finality) и почему разное количество подтверждений сети на биржах создает временной лаг при арбитраже?",
        ideal_answer_key_points=[
            "Финальность — гарантия того, что блок не может быть отменен или переписан реорганизацией цепочки.",
            "Биржи требуют разное число подтверждений (например, 12 для Ethereum, 1 для Solana/Arbitrum) перед зачислением депозита.",
            "Временной лаг перевода создает риск изменения цен на целевой бирже до зачисления средств.",
        ],
        forbidden_phrasings=["Все переводы зачисляются мгновенно"],
        source_reference="Module 04: On-Chain Logistics",
    ),

    # Модуль 5: Управление рисками, хеджирование и безопасность
    AcademyQuestion(
        id="Q-05-RISK-001",
        topic_id="05_risk_and_hedging",
        category=QuestionCategory.RISK_MANAGEMENT,
        question="Что произойдет с дельта-нейтральной позицией, если монета покажет взрывной рост на 200% за несколько часов, и как защититься от шорт-сквиза?",
        ideal_answer_key_points=[
            "Возникает риск ликвидации короткой позиции на фьючерсе, если маржинального обеспечения недостаточно.",
            "Спотовая прибыль не спасает от ликвидации шорта, если средства не перенесены в маржинальное обеспечение фьючерса.",
            "Для защиты используется консервативное плечо (1x-2x) и алгоритмическая ребалансировка обеспечения.",
        ],
        forbidden_phrasings=[
            "Ликвидация невозможна, потому что спот растет",
            "Нам не нужно следить за плечом",
        ],
        source_reference="CLAIM-002",
    ),

    # Модуль 6: Аналитический стек и психология квант-трейдинга
    AcademyQuestion(
        id="Q-06-QUANT-001",
        topic_id="06_quant_stack_and_mindset",
        category=QuestionCategory.TECHNICAL,
        question="Почему системный количественный арбитраж («закономерность, а не лотерея») математически превосходит дискреционную торговлю по сигналам в Telegram?",
        ideal_answer_key_points=[
            "Квант-подход опирается на подтвержденное математическое ожидание и закон больших чисел.",
            "Сигнальные группы продают шум без учета проскальзывания, ликвидности и комиссий тейкера.",
            "В арбитраже результат достигается одновременным закрытием спреда, а не предсказанием направления рынка.",
        ],
        forbidden_phrasings=["Сигналы могут давать 100% результат"],
        source_reference="Module 06: Quant Stack",
    ),
]


class QuestionGenerator:
    def __init__(self, db: Database):
        self.db = db

    def get_questions_by_topic(
        self, topic_id: str, count: int = 3
    ) -> List[AcademyQuestion]:
        normalized_id = TOPIC_ALIASES.get(topic_id, topic_id)
        matching = [
            q for q in CURATED_QUESTIONS
            if q.topic_id == normalized_id
            or q.topic_id == topic_id
            or (normalized_id in ("02_arbitrage_types", "02_arbitrage_and_derivatives") and q.topic_id in ("02_arbitrage_types", "02_arbitrage_and_derivatives"))
        ]
        if not matching:
            matching = CURATED_QUESTIONS
        return random.sample(matching, min(count, len(matching)))

    def get_all_questions(self) -> List[AcademyQuestion]:
        return list(CURATED_QUESTIONS)
