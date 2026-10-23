"""Curated search matrix and negative keywords for YouTube Discovery across 7 Training Days.
Hardcore institutional edition: Market Microstructure, Predatory Mechanics, MEV & Quant Execution.
"""

SEARCH_MATRIX = {
    "00_crypto_fundamentals": {
        "title": "День 1. Модуль 0: Хищная токеномика, VC-дампы и механика стейблкоинов",
        "priority": 0,
        "queries_ru": [
            "токеномика венчурные фонды разлоки слив об ритейл FDV",
            "почему падают альткоины разлоки токенов инфляция FDV",
            "механика стейблкоинов USDT USDC каскадный депег риски обеспечения",
            "мемпул блокчейна приоритет транзакций газ аукцион валидаторы",
            "как фонды разгружают токены об хомяков вестинг клифф",
        ],
        "queries_en": [
            "low float high FDV crypto VC unlock dumping retail exit liquidity",
            "predatory tokenomics vesting cliff VC dump mechanics",
            "stablecoin depeg mechanics USDT USDC liquidity pool imbalance",
            "mempool transaction ordering gas auction block building mechanics",
            "how venture capital dumps tokens on retail investors token unlocks",
        ],
        "key_terms": [
            "low float", "FDV", "exit liquidity", "token unlock", "vesting",
            "cliff", "VC dump", "depeg", "mempool", "gas auction", "USDT", "USDC"
        ]
    },
    "01_market_structure": {
        "title": "День 2. Модуль 1: Анатомия маркет-мейкеров, охота за стопами и токсичный поток",
        "priority": 1,
        "queries_ru": [
            "как маркет мейкеры манипулируют ценой охота за стопами ликвидность",
            "алгоритмы маркет мейкеров крипта спреды управление инвентарем",
            "разбор работы маркет мейкеров Wintermute Jump Trading Alameda",
            "фрагментация ликвидности криптобирж токсичный поток ордеров",
            "непостоянные потери AMM пулы ликвидности против биржевого стакана",
        ],
        "queries_en": [
            "how crypto market makers hunt liquidity stop loss order flow",
            "Wintermute Jump Trading Alameda market making mechanics forensics",
            "market making inventory risk toxic order flow Avellaneda Stoikov",
            "CEX order book vs DEX AMM impermanent loss LVR toxic flow",
            "crypto liquidity fragmentation cross exchange price inefficiency",
        ],
        "key_terms": [
            "market microstructure", "toxic flow", "inventory risk", "Wintermute",
            "Alameda", "stop hunt", "liquidity fragmentation", "LVR", "Avellaneda-Stoikov"
        ]
    },
    "02_arbitrage_and_derivatives": {
        "title": "День 3. Модуль 2: Деривативы, базис-трейдинг и почему ручной арбитраж мертв",
        "priority": 2,
        "queries_ru": [
            "почему ручной арбитраж криптовалют не работает HFT боты задержки",
            "арбитраж ставки финансирования фандинг дельта нейтральная стратегия риски",
            "спот фьючерсный базис криптоарбитраж cash and carry механика",
            "механика каскадных ликвидаций на фьючерсах открытый интерес",
            "влияние разлоков токенов на фьючерсный стакан и ставку фандинга",
        ],
        "queries_en": [
            "why retail crypto arbitrage fails latency execution slippage HFT",
            "crypto funding rate arbitrage delta neutral basis trade risks",
            "cash and carry arbitrage perpetual futures spot basis mechanics",
            "perpetual futures liquidation cascade mechanics open interest squeeze",
            "token unlock hedging perpetual futures negative funding rate",
            "HFT colocation low latency crypto arbitrage infrastructure",
        ],
        "key_terms": [
            "perpetual futures", "funding rate", "delta neutral", "basis trade",
            "cash and carry", "liquidation cascade", "latency", "HFT", "open interest"
        ]
    },
    "03_orderbook_mechanics": {
        "title": "День 4. Модуль 3: Манипуляции стаканом, спуфинг, айсберги и фейковые объемы",
        "priority": 3,
        "queries_ru": [
            "манипуляции биржевым стаканом спуфинг айсберг ордера в крипте",
            "накрутка объемов криптобирж wash trading фейковая ликвидность",
            "микроструктура стакана L2 L3 данные сведение ордеров matching engine",
            "реальная глубина стакана проскальзывание при крупных ордерах",
            "структура комиссий мейкер тейкер рибейты для маркет мейкеров",
        ],
        "queries_en": [
            "order book manipulation spoofing layering iceberg orders crypto",
            "crypto exchange wash trading fake volume detection orderbook anomalies",
            "matching engine mechanics L2 L3 order book data microstructure",
            "execution slippage orderbook depth price impact institutional execution",
            "maker rebates taker fees HFT orderbook dynamics",
        ],
        "key_terms": [
            "spoofing", "iceberg order", "layering", "wash trading", "fake volume",
            "matching engine", "L2 L3 data", "price impact", "maker rebate", "slippage"
        ]
    },
    "04_onchain_logistics": {
        "title": "День 5. Модуль 4: Темный лес ончейна, MEV-боты, сэндвич-атаки и инфраструктура",
        "priority": 4,
        "queries_ru": [
            "как работают MEV боты сэндвич атаки фронтраннинг в мемпуле",
            "темный лес блокчейна проскальзывание на DEX грабеж транзакций",
            "уязвимости смарт контрактов токенов honeypot скрытые комиссии",
            "архитектура горячих и холодных кошельков бирж ребалансировка ликвидности",
            "финальность блоков реорганизация цепи риски депозитов на биржу",
        ],
        "queries_en": [
            "MEV sandwich attacks frontrunning mempool bots onchain execution DEX",
            "Ethereum dark forest Flashbots MEV searcher builder validator mechanics",
            "JIT liquidity DEX slippage toxic arbitrage AMM pools",
            "crypto exchange hot cold wallet architecture sweeping rebalancing",
            "smart contract token traps honeypot malicious transfer tax forensics",
        ],
        "key_terms": [
            "MEV", "sandwich attack", "frontrunning", "Flashbots", "dark forest",
            "mempool", "JIT liquidity", "honeypot", "wallet sweeping", "reorg"
        ]
    },
    "05_risk_and_hedging": {
        "title": "День 6. Модуль 5: Анатомия краха бирж, ловушки выводов, Leg Risk и AML",
        "priority": 5,
        "queries_ru": [
            "банкротства криптобирж фейковый proof of reserves дыры в балансе",
            "заморозка вывода средств на биржах при арбитраже ловушки ликвидности",
            "риск исполнения второй ноги в арбитраже проскальзывание рассинхрон",
            "блокировка средств по AML KYT на криптобирже грязная крипта миксеры",
            "хеджирование волатильности и риска контрагента в криптотрейдинге",
        ],
        "queries_en": [
            "crypto exchange insolvency proof of reserves fake volume withdrawal freeze",
            "execution leg risk cross exchange arbitrage broken hedge latency",
            "honeypot crypto exchanges fake arbitrage spread withdrawal trap",
            "institutional crypto AML KYT chainalysis freeze compliance risks",
            "counterparty risk FTX collapse forensics exchange balance sheet hole",
        ],
        "key_terms": [
            "insolvency", "Proof of Reserves", "withdrawal freeze", "leg risk",
            "honeypot exchange", "AML KYT", "Chainalysis", "counterparty risk"
        ]
    },
    "06_quant_stack_and_mindset": {
        "title": "День 7. Модуль 6: Квант-стек, алгоритмическое преимущество и смерть теханализа",
        "priority": 6,
        "queries_ru": [
            "почему технический анализ и паттерны не работают математика рынка",
            "архитектура скринеров арбитража WebSocket API стакан в реальном времени",
            "количественный трейдинг против интуитивного математическое ожидание",
            "анализ спредов и синтетических пар в TradingView формулы",
            "почему 99 процентов трейдеров теряют деньги ошибка выжившего",
        ],
        "queries_en": [
            "Chat With Traders crypto quant market making HFT execution",
            "why technical analysis fails quantitative finance statistical edge",
            "real time crypto arbitrage engine WebSocket orderbook API architecture",
            "TradingView synthetic spread chart basis ratio quantitative analysis",
            "why crypto signal groups fail negative expected value retail traps",
        ],
        "key_terms": [
            "Chat With Traders", "quantitative trading", "expected value", "WebSocket API",
            "statistical edge", "synthetic spread", "market inefficiency", "quant"
        ]
    }
}

# Alias for backward compatibility
SEARCH_MATRIX["02_arbitrage_types"] = SEARCH_MATRIX["02_arbitrage_and_derivatives"]

# Стоп-слова для первичного фильтра заголовков (отсекаем инфоцыган и детский ликбез на входе)
NEGATIVE_KEYWORDS = [
    # Инфоцыганство и скам-сигналы
    "связка дня",
    "бесплатная связка",
    "гарантированный доход",
    "без вложений",
    "100% прибыль",
    "сигналы в телеграм",
    "раскрутка счета",
    "пассивный доход на автомате",
    "free money",
    "guaranteed profit",
    "100x gem",
    "telegram signals",
    "памп и дамп",
    "1000x",
    "заработок для новичка с нуля",
    "100% гарантия",
    "best signals",
    "реферальная ссылка",
    "t.me/",
    # Поверхностный контент для новичков и ритейл-гадания
    "простыми словами",
    "для начинающих",
    "для чайников",
    "с нуля",
    "за 3 минуты",
    "за 5 минут",
    "for beginners",
    "whiteboard crypto",
    "explained simply",
    "прогноз цены",
    "прогноз курса",
    "price prediction",
    "технический анализ биткоин",
    "куда пойдет биткоин",
]
