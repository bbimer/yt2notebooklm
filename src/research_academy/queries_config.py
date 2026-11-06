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

# Матрица целевых поисковых запросов для Web Harvester (3 институциональных кластера на модуль)
WEB_SEARCH_MATRIX = {
    "00_crypto_fundamentals": {
        "title": "День 1. Модуль 0: Фундамент крипты, блокчейн и токеномика",
        "priority": 0,
        "web_queries": [
            # Кластер 1: L1 Coin vs Token & Механика мемпула / газа (Hard Specs)
            "EIP-20 token standard formal specification state contract ethereum",
            "EIP-1559 fee market base fee priority fee specification ethereum",
            "mempool transaction ordering gas auction PBS proposer builder separation mechanics",
            # Кластер 2: Стейблкоины: структура резервов, кредитный риск и механика депега в пулах
            "USDT USDC reserve composition treasury bills maturity credit risk redemption gate",
            "stablecoin depeg mechanics Curve StableSwap pool imbalance liquidity crisis",
            # Кластер 3: Венчурная токеномика: Low Float / High FDV, стейкинг-лазейки и Secondary OTC
            "Low Float High FDV tokenomics venture capital unlock overhang institutional research",
            "locked token staking rewards dilution insider dump tokenomics mechanics",
            "crypto secondary OTC market locked tokens SAFT discount hedging mechanics",
        ],
        "key_terms": [
            "blockchain", "mempool", "gas fee", "stablecoin", "USDT", "USDC",
            "ERC20", "TRC20", "tokenomics", "FDV", "market cap", "token unlock"
        ],
    },
    "01_market_structure": {
        "title": "День 2. Модуль 1: Архитектура рынка, биржи и маркет-мейкеры",
        "priority": 1,
        "web_queries": [
            # Кластер 1: Спецификации биржевых ядер, AMM инварианты и тиковая математика
            "Uniswap v3 concentrated liquidity math virtual reserves tick spacing formal specification",
            "AMM constant product invariant x y k slippage price impact derivation",
            "Avellaneda Stoikov high frequency market making optimal bid ask spread inventory risk",
            # Кластер 2: Unit-экономика и метрики институционального маркет-мейкинга
            "loss versus rebalancing LVR metric automated market maker toxic flow Milionis",
            "VPIN volume synchronized probability of toxicity order flow microstructure",
            "crypto exchange maker rebate taker fee tier volume requirements institutional prime broker",
            # Кластер 3: Судебные прецеденты, манипуляции и токсичный поток (Forensics & Enforcement)
            "crypto token loan agreement TLA call option market maker Wintermute DWF Labs structure",
            "SEC enforcement action crypto market maker wash trading manipulation complaint",
            "South Korea crypto exchange foreign exchange control Kimchi Premium capital flight arbitrage",
        ],
        "key_terms": [
            "CEX", "DEX", "AMM", "liquidity pool", "order book", "market maker",
            "spread", "slippage", "arbitrage", "Wintermute", "Jump Trading",
            "toxic flow", "LVR", "Kimchi Premium"
        ],
    },
    "02_arbitrage_and_derivatives": {
        "title": "День 3. Модуль 2: Деривативы, бессрочные фьючерсы и арбитраж",
        "priority": 2,
        "web_queries": [
            # Кластер 1: Спецификации фьючерсных ядер: Mark Price, Funding Rate & ADL
            "perpetual futures funding rate calculation formula premium index clamp Binance Bybit spec",
            "Mark Price calculation median price basis moving average liquidation trigger mechanism",
            "auto deleveraging ADL ranking formula effective leverage profit tier exchange specification",
            # Кластер 2: Unit-экономика базис-трейдинга и дельта-нейтрального хеджирования
            "cash and carry basis trade delta neutral yield funding rate annualized return fee decomposition",
            "portfolio margin UTA Unified Trading Account margin efficiency cross collateral liquidation threshold",
            "funding rate bleed long squeeze negative funding cost of carry crypto basis trade",
            # Кластер 3: Расследования судебных кейсов и крахов алгоритмических систем (Forensics)
            "Mango Markets exploit Avraham Eisenberg perpetual futures oracle manipulation DOJ indictment",
            "Ethena USDe reserve fund stress test negative funding rate duration risk contagion analysis",
            "perpetual futures cascading liquidations liquidation cascade BitMEX March 2020 post-mortem",
        ],
        "key_terms": [
            "perpetual futures", "funding rate", "basis trade", "delta-neutral",
            "cash-and-carry", "liquidation", "Mark Price", "ADL", "UTA",
            "portfolio margin", "cross margin", "isolated margin", "Mango Markets"
        ],
    },
    "03_orderbook_mechanics": {
        "title": "День 4. Модуль 3: Микроструктура биржевого стакана и поток ордеров",
        "priority": 3,
        "web_queries": [
            # Кластер 1: Архитектура биржевых движков, Level 3 фиды и модели импакта
            "exchange matching engine deterministic price-time FIFO execution queue specification",
            "Level 3 market data feed MBO market by order ITCH OUCH protocol crypto exchange",
            "Kyle Lambda market impact model Kyle 1985 continuous auction informed trading",
            "Almgren Chriss optimal execution liquidation of portfolio market impact parameters",
            # Кластер 2: Unit-экономика исполнения крупных блоков и декомпозиция скрытых ордеров
            "iceberg order detection algorithm native exchange iceberg display size fee structure",
            "maker taker rebate schedule liquidity extraction fee impact net spread decomposition",
            "order book depth slippage integration cost calculation multi-tick liquidation curve",
            # Кластер 3: Криминалистика маркет-манипуляций и судебные кейсы (Forensics & Indictments)
            "DOJ FBI Operation Token Mirrors crypto market maker indictment NexFundAI Gotbit CLS Global ZM Quant",
            "order book spoofing layering detection algorithm CFTC enforcement crypto",
            "wash trading detection Benford law order volume distribution forensic analysis cryptocurrency",
        ],
        "key_terms": [
            "Level 2", "Level 3", "orderbook", "matching engine", "price-time priority",
            "FIFO", "Kyle Lambda", "Almgren-Chriss", "market impact", "slippage",
            "iceberg order", "spoofing", "layering", "wash trading", "Operation Token Mirrors"
        ],
    },
    "04_onchain_logistics": {
        "title": "День 5. Модуль 4: Блокчейн-инфраструктура и ончейн-логистика",
        "priority": 4,
        "web_queries": [
            # Кластер 1: Финальность L1/L2, механика секвенсоров и архитектура смарт-контрактов
            "Ethereum Gasper consensus Casper FFG LMD GHOST finality epoch slot reorg probability",
            "Arbitrum Nitro Optimism Bedrock sequencer batch poster fraud proof validity proof latency",
            "EIP-1967 transparent upgradeable proxy storage slots implementation fallback delegatecall",
            # Кластер 2: Unit-экономика межсетевой логистики и децентрализованного клиринга
            "centralized exchange hot wallet deposit address batch consolidation sweep gas fee economics",
            "Circle CCTP Cross-Chain Transfer Protocol burn mint attestation latency vs lock and mint bridge",
            "L2 gas breakdown execution fee L1 data availability blob fee EIP-4844 cost model",
            # Кластер 3: Форензика эксплойтов мостов и компрометации валидаторов (Post-Mortems)
            "Ronin Bridge validator key compromise 625M exploit Lazarus Group post-mortem forensics",
            "Nomad bridge replica contract uninitialized zero hash verification exploit post-mortem",
            "Multichain bridge exploit 126M MPC private key compromise admin centralization post-mortem",
        ],
        "key_terms": [
            "Gasper finality", "L1 vs L2", "centralized sequencer", "bridge security",
            "CCTP", "burn and mint", "lock and mint", "EIP-1967 proxy", "Ronin exploit",
            "Multichain post-mortem", "deposit confirmation time", "hot wallet sweep"
        ],
    },
    "05_risk_and_hedging": {
        "title": "День 6. Модуль 5: Управление рисками, хеджирование и безопасность",
        "priority": 5,
        "web_queries": [
            # Кластер 1: Инфраструктурные задержки (Latency), Legging Risk и протоколы защиты исполнения
            "multi-leg arbitrage execution risk legging risk partial fill asynchronous latency",
            "Equinix TY3 Tokyo co-location cross-connect round trip time RTT Cancel-on-Disconnect COD",
            "exchange API rate limit ban WebSocket stale book data race condition mitigation",
            # Кластер 2: Стандарты ончейн-мониторинга (AML / KYT), скоринг риска и принудительная блокировка
            "Chainalysis TRM Labs Elliptic KYT risk score taint analysis hop clustering methodology",
            "Tether USDT Circle USDC blacklist freeze smart contract function OFAC SDN compliance",
            "FATF Travel Rule VASP crypto exchange compliance withdrawal freeze AML audit trigger",
            # Кластер 3: Оценка риска контрагента, банкротства бирж и отсев проблемных/Honeypot-шлюзов
            "FTX Alameda Research bankruptcy balance sheet contagion counterparty risk post-mortem",
            "DOJ FinCEN Bitzlato Garantex Tornadocash enforcement action tainted liquidity contagion",
            "fake crypto exchange honeypot withdrawal freeze liquidity trap forensics",
        ],
        "key_terms": [
            "hedging", "perpetual futures", "execution risk", "latency", "AML KYT",
            "counterparty risk", "honeypot", "withdrawal freeze", "legging risk",
            "Cancel-on-Disconnect", "taint analysis", "OFAC compliance"
        ],
    },
    "06_quant_stack_and_mindset": {
        "title": "День 7. Модуль 6: Аналитический стек и психология квант-трейдинга",
        "priority": 6,
        "web_queries": [
            # Кластер 1: Построение синтетических спредов, коинтеграция и математика стат-арбитража
            "TradingView synthetic spread chart math operator custom pair ratio basis visualization",
            "statistical arbitrage pairs trading cointegration Augmented Dickey-Fuller Ornstein-Uhlenbeck Z-score",
            "cross-exchange lead-lag price discovery information share Hasbrouck metric crypto",
            # Кластер 2: Автоматизация сбора данных по API (WebSocket L2/L3) и архитектура скринеров
            "crypto arbitrage screener architecture async WebSocket orderbook snapshot delta synchronization",
            "CCXT Pro high frequency order book streaming REST vs WebSocket latency benchmark",
            "real-time net spread calculation maker taker fee withdrawal cost orderbook depth walk",
            # Кластер 3: Математика неизбежной просадки при отрицательном EV (Gambler's Ruin) и крах сигнальных групп
            "expected value EV math trading transaction friction decay Gambler Ruin probability formula",
            "Kelly criterion optimal f position sizing drawdown risk of ruin quantitative trading",
            "crypto pump and dump signal groups Telegram empirical analysis negative expectation arXiv",
        ],
        "key_terms": [
            "TradingView spread", "arbitrage screener", "orderbook API",
            "quantitative trading", "discretionary", "statistical edge",
            "cointegration", "expected value EV", "Gambler Ruin", "Kelly criterion"
        ],
    },
}

# Alias for backward compatibility
WEB_SEARCH_MATRIX["02_arbitrage_types"] = WEB_SEARCH_MATRIX["02_arbitrage_and_derivatives"]

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
    "курс по крипте",
    "купить связку",
    "арбитраж p2p связка",
    "крипта для новичков",
    "пассивный заработок",
    "слив курсов",
    "лёгкие деньги",
    "легкие деньги",
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
