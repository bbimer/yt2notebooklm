# The Curious Case of Token Unlocks - Delphi Digital

- **URL:** https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks
- **Канал / Автор:** members.delphidigital.io
- **Домен:** crypto
- **Тематический модуль:** 00_crypto_fundamentals
- **Рейтинг Gatekeeper:** 9.5/10
- **Статус проверки:** Проверено (Methodist Verified)

---

## 🏛 СЛОЙ 1: ФУНДАМЕНТАЛЬНАЯ РЫНОЧНАЯ БАЗА (MARKET REALITY)

### Краткое содержание
Отчёт Delphi Digital (Priyansh Patel, 02.12.2022) — это институциональная анатомия главного хищнического механизма крипторынка: разлоков токенов. Ключевой тезис: FDV — это метрика предложения, а не «страшилка»; MC — метрика текущего публичного спроса. Их отношение FDV/MC — это множитель, на который вырастет предложение и, соответственно, давление продаж. Отчёт разбирает плейбук Low Float / High FDV: венчурные фонды входят по $0.05 при оценке $200M, проект выходит на биржу с 1% саплая в обороте, FDV раздувается до $2B–$20B, а через 6 месяцев клффа начинается анлок, где инвестор продаёт даже после -80%, потому что он всё ещё +20x. Показаны реальные кейсы: FLOW (300M токенов = 6x саплая, до $5.1B давления), Radix (5x саплая, флеш-крэш -90%), Oasis и Nym (экосистемные фонды за 1–2 дня до анлока как генератор exit liquidity), Solana (исключение — живой OTC-рынок с дисконтом 60–80% и <2% саплая в обороте), ICP (перпы за 5 дней до спота, $170M OI против $110B инвесторской аллокации), AXS и APE («бычьи анлоки» как unwind хеджей, а не реальный спрос). Отдельно разобран стейкинг как ловушка: 100% APY в нативном токене — это не доход, а разводнение плюс ценовой риск плюс lock-up, превращающий держателя в заложника. Вывод автора: время-ориентированные анлоки должны быть заменены на milestone-based. ВАЖНО: источник — письменный отчёт, а не видео, поэтому таймкоды в key_claims являются секционно-маппированными аппроксимациями (SEC-01≈00:00, SEC-02≈00:45, SEC-03≈03:00, SEC-04≈10:20, SEC-05≈13:20, SEC-06≈17:30, SEC-07≈25:00), а не реальными секундами видеоряда.

### Ключевые концепции
- FDV как метрика предложения (Supply Metric) против MC как метрики спроса (Demand Metric)
- Коэффициент FDV/MC — множитель будущего расширения предложения
- Плейбук Low Float / High FDV: клфф → анлок → каскадное давление продаж
- Exit Liquidity: розничный покупатель как выход для венчурного капитала
- Emission-adjusted revenue (Revenue / Token Emissions) как метрика здоровья токеномики
- Стейкинг нативного токена как замаскированное разводнение (Dilution Trap)
- Liquidity Ceiling: физический предел выхода из позиции при тонком пуле
- Lock-up асимметрия: запертый стейкер (User A) против свободного держателя (User B)
- OTC-дески как механизм разгрузки без давления на вторичный рынок
- Хеджирование заблокированных токенов через бессрочные фьючерсы (Perp Hedging)
- «Бычий анлок» как отыгранный заранее медвежий анлок (Priced-in Bearish Unlock)
- Announcement Pump: позитивный нарратив за 1–2 дня до анлока как генератор ликвидности
- Cumulative Volume Delta (CVD) как подпись хеджеров на споте и перпах
- Supply Overhang: навес предложения, который рынок не может переварить
- Milestone-based unlocks как альтернатива time-based unlocks

### Объяснение механизмов
Механика разлока — это не событие, а многофазный процесс перераспределения риска от инсайдеров к ритейлу. Фаза 1 (Pre-Launch): проект рейзит $10M у фондов при оценке $200M, цена токена для инсайдера — $0.05, клфф 6 месяцев, вестинг 12 месяцев. На листинг выходит 1% саплая (эйрдроп, ликвидность, реварды). При публичном спросе $20M капитализация = $20M, но FDV = $2B, цена $0.5 — инвестор уже +10x. Фаза 2 (Нарратив): приток $180M спекулятивного спроса разгоняет FDV до $20B, цена $5, инвестор +100x. Фаза 3 (Анлок): через 6 месяцев начинается вестинг, за 12 месяцев предложение вырастает в 100 раз. Инвестор продаёт непрерывно даже после -80%, потому что его себестоимость $0.05, а он всё ещё +20x. Команда с 30% аллокацией при той же цене держит $1.2B и готова забрать треть за 18 месяцев «работы». Фаза 4 (Хедж): если по активу есть перпы, инсайдеры шортят фьючерс против заблокированного спота, фиксируя цену выхода. Ограничитель — ликвидность: на ICP $170M OI против $110B инвесторской аллокации (покрытие ~0.15%), на OXY OI никогда не превышал $14.4M против $4B позиции инвесторов (покрытие ~0.36%). Фаза 5 (Unwind): в день анлока хеджеры разворачивают фьючерсы и одновременно продают спот. Шортисты-спекулянты, ставившие на дамп, вынуждены закрываться — отсюда «бычьи анлоки» AXS (+19%) и APE (+40%). Это не спрос, это технический unwind. Параллельный канал — OTC: SAFT Solana торговались с дисконтом 60–80% до анлока, страх выкупался фондами с высокой conviction, их кост-база становилась 2–4x, а в обороте оставалось <2% саплая — рефлексивность дала параболический рост +25,000%. Третий канал — управление нарративом: Oasis объявил экосистемный фонд на $160M за 2 дня до расширения предложения на 133%, цена удвоилась перед анлоком и упала вдвое после; Nym объявил $300M за день до анлока, цена рухнула на 70% за 9 дней. Отдельная ловушка — стейкинг: 100% APY выплачивается в том же токене, то есть держатель финансирует собственную дилюцию; при падении цены с $1 до $0.3 двойное количество токенов даёт $60 вместо $100. Плюс Liquidity Ceiling: если в пуле $100k USDT, а саплай 200k XYZ, выйти могут только первые продавцы — начинается race to the exits. Плюс lock-up: пока User A заперт в стейкинг-модуле, User B продаёт на -60%, и A выходит уже на -80% с двойным количеством обесцененных токенов.

### Терминология и сленг практиков
- **Low Float / High FDV**: Схема, при которой в свободном обращении находится 1–10% саплая, а оценка по полной эмиссии раздута в десятки раз. Используется для удержания высокой цены на старте и максимизации выручки инсайдеров при последующих анлоках.
- **FDV (Fully Diluted Valuation)**: Оценка проекта по всей эмиссии, включая заблокированные токены. В отчёте трактуется строго как метрика предложения (supply metric), а не как «абстрактная цифра».
- **MC (Market Cap)**: Оценка по токенам в обращении. Трактуется как метрика текущего публичного спроса (demand metric).
- **FDV/MC Ratio**: Множитель, на который вырастет предложение токена. Если FDV/MC = 20, рынку нужно увеличить публичный спрос в 20 раз, чтобы удержать цену.
- **Cliff (Клфф)**: Период полной блокировки токенов инсайдеров после листинга (в примере — 6 месяцев). До его окончания продаж нет, после — начинается лавина.
- **Vesting / Unlock**: График постепенного высвобождения заблокированных токенов. В отчёте подчёркнуто: анлок — процесс, а не единичное событие.
- **Exit Liquidity**: Розничные покупатели и спекулятивный спрос, которые обеспечивают инсайдерам возможность выйти из позиции по приемлемой цене. Прямая формулировка автора: «create exit liquidity for potential sellers».
- **Emission-adjusted Revenue**: Отношение выручки протокола к долларовой стоимости эмиссии токенов. GMX — 2x, SUSHI — 7.6x. Показывает, переживёт ли протокол окончание инцентивов.
- **Supply Overhang**: Навес будущего предложения, который давит на цену и не даёт активам отскакивать даже на общем восстановлении рынка.
- **OTC Desk / SAFT OTC**: Внебиржевая торговля токенами через дилерскую сеть, не отражающаяся на вторичном рынке. На Solana SAFT продавались с дисконтом 60–80% до анлока.
- **Perp Hedging**: Шорт в бессрочном фьючерсе против заблокированного спота. Позволяет инсайдеру зафиксировать цену выхода до анлока. Ограничен доступной ликвидностью и OI.
- **Open Interest (OI)**: Совокупный объём открытых фьючерсных позиций. В отчёте используется как индикатор того, сколько инсайдеры реально смогли захеджировать.
- **Funding Rate**: Ставка финансирования. Резко отрицательный фандинг перед анлоком — подпись массового шорта (хеджеров и спекулянтов).
- **CVD (Cumulative Volume Delta)**: Индикатор, растущий при исполнении лимитных продаж и падающий при исполнении лимитных покупок. В отчёте используется как доказательство одновременного unwind фьючерсов и продажи спота.
- **Announcement Pump**: Позитивное объявление (экосистемный фонд, партнёрство) за 1–2 дня до анлока, разгоняющее цену и создающее ликвидность для продавцов.
- **Bullish Unlock**: Рост цены после анлока. В отчёте деконструируется: это не спрос, а отыгранный заранее медвежий анлок плюс вынужденное закрытие шортистов.
- **Reflexivity (Рефлексивность)**: Механизм, при котором рост цены сам по себе привлекает новых покупателей. На Solana запустил параболический рост при <2% саплая в обороте.
- **Race to the Exits**: Ситуация, когда держатели одновременно пытаются выйти из тонкого пула ликвидности. Первые продавцы фиксируют бумажную прибыль, остальные получают обесцененный остаток.
- **Milestone-based Unlock**: Предложение автора: привязывать разблокировку к достижению метрик (объём, TVL, пользователи), а не к календарю.


### Числовые примеры и расчеты
- Стейкинг-ловушка: стейкаем $100 в XYZ под 100% APY при цене $1 → получаем 100 XYZ, через год 200 XYZ. Если цена упала до $0.3, портфель стоит $60 против изначальных $100. Потеря 40% при «удвоении количества токенов».
- Liquidity Ceiling: саплай 100k XYZ, в пуле $100k USDT. Даже если держатель владеет всем саплаем, он может вывести максимум $100k — цена при этом будет уничтожена. Через год при 100% застейканного саплая предложение 200k XYZ, но exit-динамика та же: первые продавцы забирают всё, остальные — race to the exits.
- Lock-up асимметрия: User A застейкал, User B — нет. Плохие новости, цена -60%. B продаёт с небольшим убытком. A заперт; к моменту разблокировки цена -80%, и даже с двойным количеством токенов долларовая стоимость инвестиции существенно ниже.
- Плейбук Low Float / High FDV: рейз $10M при оценке $200M → цена для инвестора $0.05. Стартовый саплай 1%, публичный спрос $20M → MC $20M, FDV $2B, цена $0.5, инвестор +10x. Приток $180M спроса → FDV $20B, цена $5, инвестор +100x. Через 6 месяцев клфф и 12 месяцев вестинга: предложение растёт в 100 раз. Инвестор продаёт даже после -80%, оставаясь +20x. Аллокация команды 30% при той же цене = $1.2B.
- FIDA (Bonfida): -97.9% от максимума при 10% саплая в обороте. Цена приватной продажи $0.1 — инвестор всё ещё в плюсе 3.8x.
- GMT (STEPN): -90.5% при 6.03% саплая в обороте. Цена приватной продажи $0.005 — инвестор всё ещё в плюсе 75x.
- FLOW, 15.10.2021: открытие $17.68, минимум дня $9.2 (Kraken) и ~$6.1 (CoinList) — падение 48–65%. Разлок 300M FLOW = 6x от circulating supply, потенциальное давление продаж до $5.1B. Инвесторы всё равно +100x.
- Radix DLT, 15.09.2021: circulating supply 1.89B → 9.6B (5x). Флеш-крэш более -90%, затем отскок +800% от минимума, новый ATH $0.687 (+55x от лоу).
- Oasis Network: экосистемный фонд $160M объявлен за 2 дня до расширения предложения на 133% (1.471B ROSE). Инвесторы ~51.6%, core contributors ~20.3%, community/ecosystem ~27.6%. Цена удвоилась перед анлоком и упала вдвое в последующие дни.
- Nym: экосистемный фонд $300M объявлен за день до анлока 80.75M NYM (инвесторы ~60.3%, команда ~30.9%). Предложение выросло в 2.3x, цена упала более чем на 70% за 9 дней.
- Solana: аллокация community всего 1.6% саплая. Цена продажи $0.04 (seed) — $0.25 (strategic). Предложение должно было вырасти более чем в 7x при апсайде инвесторов 10–60x. Вместо дампа — рост более 25,000% от ATL до ATH за счёт OTC-рынка с дисконтом 60–80% и кост-базой покупателей 2–4x.
- ICP: перпы запущены за 5 дней до спота. Инвесторы ~37% саплая, команда/фаундеры ~62%, community ~1%. Цена: seed $0.035, strategic $0.63, presale $4.17. ATH $2,831 (Binance) / $630 (Coinbase) → апсайд 151x–18,000x. Инвесторская аллокация оценена ~$110B, команда ~$183B. OI $170M при экстремально отрицательном фандинге — покрытие хеджа ~0.15% от аллокации инвесторов.
- OXY: инвесторы +110x на максимуме, 1B токенов = более $4B. OI на контракте никогда не превышал $14.4M — покрытие ~0.36%. IEO-цена $0.10, ритейл был +44x и фиксировал прибыль; даунтренд вызван не хеджем, а отсутствием инкрементальных покупателей.
- AXS, 25.10.2022: ~21.5M токенов (~$273M) к разлоку. Инвесторы ~9.2%, стейкинг-реварды ~22.7%, команда ~26.6%, play-to-earn ~21.9%, экосистема ~7.8%, советники ~11.65%. OI вырос до $193M за день до анлока при агрессивно отрицательном фандинге, затем откатился к пред-анлоковым уровням. Цена выросла почти на 19%.
- APE: ~77.3% разблокированных токенов принадлежали инвесторам. За 3 дня до анлока цена -20%, OI $117M. В день анлока OI упал до $84M, фандинг ушёл в минус. Сразу после анлока OI начал расти, APE прибавил более 40%.
- LooksRare: стратегические инвесторы через passive staking забрали $38.04M (расчёт по формуле [(33M/кол-во застейканных)*объём торгов за день] с 10.01.2022 по 15.07.2022). Команда заработала более 20,151 WETH (~$31.5M). Дополнительно команда, казна и инвесторы получают на 5.2%, 6.9% и 12% больше токенов, чем указано в документации, если держат стейк до последнего дня эмиссии.
- Aptos: community составляет лишь 2.85% застейканного саплая, остальные стейкхолдеры — более 97%. При пропорциональном распределении стейкинг-ревардов community получит 23.4M APT против 798M+ APT, уходящих стейкхолдерам. Инфляция 7% годовых с понижением на 1.5% до терминальной ставки 3.5%.
- GMX: выручка вдвое превышает долларовую стоимость эмиссии токенов, 30% комиссий со свопов и маржинальной торговли распределяются стейкерам GMX. SUSHI: выручка в 7.6x превышает стоимость эмиссии, но тренд нисходящий из-за ухудшающихся фундаментальных показателей.

---

## 🔍 СЛОЙ 2: АУДИТ ИСТОЧНИКА И ЦИТАТЫ (SOURCE EVIDENCE)

### Проверяемые утверждения и цитаты
- **[UNVERIFIED]** Трейдер GCR в конце прошлого цикла целенаправленно искал монеты с крупными предстоящими анлоками и открывал по ним шорты, зарабатывая на продажах инвесторов после разблокировки.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=45s (00:45)
  - Цитата автора: *«Towards the end of the last cycle, GCR was focused on finding coins with massive upcoming unlocks and taking short positions on them to profit when investors sold their unlocked tokens.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Трейдер GCR в конце прошлого цикла целенаправленно искал монеты с крупными предстоящими анлоками и открывал по ним шорты, зарабатывая на продажах инвесторов после разблокировки.»*
- **[UNVERIFIED]** Структура распределения токенов сместилась от равных условий ICO к среде, где профессиональные инвесторы имеют огромное преимущество: большие аллокации и значительно более низкая себестоимость против ритейла.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=60s (01:00)
  - Цитата автора: *«Despite the negative connotations, ICOs provided a level playing field where most participants invested in a project at the same cost. However, in the past couple of years, the environment has shifted to one where professional investors have a massive edge – from increased allocations to a significantly lower cost basis versus retail investors.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Структура распределения токенов сместилась от равных условий ICO к среде, где профессиональные инвесторы имеют огромное преимущество: большие аллокации и значительно более низкая себестоимость против ритейла.»*
- **[UNVERIFIED]** Emission-adjusted revenue (отношение выручки к долларовой стоимости эмиссии токенов) — метрика здоровья токеномики: у GMX выручка вдвое превышает эмиссию, у SUSHI — в 7.6 раза, но тренд нисходящий из-за ухудшения фундаментальных показателей.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=200s (03:20)
  - Цитата автора: *«GMX has 2x revenue compared to token emissions... The revenue/token emission ratio is quite high, second only to Uniswap, with revenue being 7.6x the dollar value of emissions. Yet, the deteriorating fundamentals have resulted in the ratio trending downwards.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Emission-adjusted revenue (отношение выручки к долларовой стоимости эмиссии токенов) — метрика здоровья токеномики: у GMX выручка вдвое превышает эмиссию, у SUSHI — в 7.6 раза, но тренд нисходящий из-за ухудшения фундаментальных показателей.»*
- **[UNVERIFIED]** LooksRare: стратегические инвесторы через passive staking забрали $38.04M, команда заработала более 20,151 WETH (~$31.5M). Команда, казна и инвесторы получают на 5.2%, 6.9% и 12% больше токенов, чем указано в документации, если держат стейк до конца эмиссии.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=400s (06:40)
  - Цитата автора: *«Running this formula from Jan. 10, 2022 to Jul. 15, 2022, we get $38.04M. Even though the strategic sale investors did not benefit by receiving additional LOOKS, they did pocket one-third of the current market cap from passive staking. The team also earned over 20,151 WETH (~$31.5M at the current market price) to date.»*
  - Формулировка для менеджера: *«По утверждению автора видео: LooksRare: стратегические инвесторы через passive staking забрали $38.04M, команда заработала более 20,151 WETH (~$31.5M). Команда, казна и инвесторы получают на 5.2%, 6.9% и 12% больше токенов, чем указано в документации, если держат стейк до конца эмиссии.»*
- **[UNVERIFIED]** Aptos: community составляет лишь 2.85% застейканного саплая, остальные стейкхолдеры — более 97%. При пропорциональном распределении стейкинг-ревардов community получит 23.4M APT против 798M+ APT, уходящих стейкхолдерам, что превращает governance в фасад.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=560s (09:20)
  - Цитата автора: *«The community makes up only 2.85% of the staked supply, whereas the other stakeholders make up over 97%... the 'community' will receive 23.4M APT, which dwarfs in comparison to the 798M+ APT tokens going to stakeholders... Given that Aptos makes up the majority, governance rights become a facade.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Aptos: community составляет лишь 2.85% застейканного саплая, остальные стейкхолдеры — более 97%. При пропорциональном распределении стейкинг-ревардов community получит 23.4M APT против 798M+ APT, уходящих стейкхолдерам, что превращает governance в фасад.»*
- **[UNVERIFIED]** Стейкинг под высокий APY в нативном токене — это не доход, а разводнение плюс ценовой риск. При падении цены с $1 до $0.3 двойное количество токенов даёт $60 вместо $100.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=640s (10:40)
  - Цитата автора: *«If the price of XYZ was $1 when I initially staked, I would get 100 XYZ. After a year, I would have 200 XYZ from the yield I received. But, this comes with a faulty assumption that the token price will remain the same... it is quite feasible that the price of XYZ becomes $0.3, in which case my 200 XYZ would now be worth less than my initial dollar value of the investment.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Стейкинг под высокий APY в нативном токене — это не доход, а разводнение плюс ценовой риск. При падении цены с $1 до $0.3 двойное количество токенов даёт $60 вместо $100.»*
- **[UNVERIFIED]** Существует физический предел выхода: если в пуле $100k USDT, а саплай 200k XYZ, вывести смогут только первые продавцы — начинается race to the exits, и цена уничтожается.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=700s (11:40)
  - Цитата автора: *«If the liquidity pool has $100k of USDT (or equivalent), then even if an individual holds the entire supply, they can only cash out $100k. The price of the token would be decimated... The first few sellers might be able to realize their paper profits, effectively creating a race to the exits.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Существует физический предел выхода: если в пуле $100k USDT, а саплай 200k XYZ, вывести смогут только первые продавцы — начинается race to the exits, и цена уничтожается.»*
- **[UNVERIFIED]** Lock-up в стейкинге создаёт асимметрию: свободный держатель продаёт на -60%, а запертый стейкер выходит на -80% с двойным количеством обесцененных токенов.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=760s (12:40)
  - Цитата автора: *«User B was quick to act and could sell at a slight loss. User A had their tokens stuck in the staking module and could not sell. By the time they received their tokens, the price had fallen 80%, and even though they held double the number of tokens, the net dollar value of the investment was significantly less.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Lock-up в стейкинге создаёт асимметрию: свободный держатель продаёт на -60%, а запертый стейкер выходит на -80% с двойным количеством обесцененных токенов.»*
- **[UNVERIFIED]** FDV — это метрика предложения, MC — метрика спроса. Отношение FDV/MC показывает, во сколько раз должно вырасти предложение и, соответственно, публичный спрос для удержания цены.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=820s (13:40)
  - Цитата автора: *«The other side believes that if the market cap is the current size of the public demand, then low-float projects need to increase the public demand for their token by several orders of magnitude to maintain the same price. Therefore, if market cap is a demand metric, then FDV is a supply metric. The ratio of FDV/MC serves as the multiple by which the supply is set to expand.»*
  - Формулировка для менеджера: *«По утверждению автора видео: FDV — это метрика предложения, MC — метрика спроса. Отношение FDV/MC показывает, во сколько раз должно вырасти предложение и, соответственно, публичный спрос для удержания цены.»*
- **[UNVERIFIED]** Плейбук Low Float / High FDV: рейз $10M при оценке $200M по $0.05 за токен, 1% саплая в обороте, $20M публичного спроса → FDV $2B, инвестор +10x. Приток $180M спроса → FDV $20B, инвестор +100x. Через 6 месяцев клфф и 12 месяцев вестинга предложение растёт в 100 раз, инвестор продаёт даже после -80%, оставаясь +20x.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=880s (14:40)
  - Цитата автора: *«Fast-forward to 6 months after launch, when the investor and team tokens begin to unlock. In just the next 12 months, the supply will increase by 100x. Investors will sell relentlessly even after an 80% drop, as they are still up 20x.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Плейбук Low Float / High FDV: рейз $10M при оценке $200M по $0.05 за токен, 1% саплая в обороте, $20M публичного спроса → FDV $2B, инвестор +10x. Приток $180M спроса → FDV $20B, инвестор +100x. Через 6 месяцев клфф и 12 месяцев вестинга предложение растёт в 100 раз, инвестор продаёт даже после -80%, оставаясь +20x.»*
- **[UNVERIFIED]** FIDA упала на 97.9% при 10% саплая в обороте, GMT — на 90.5% при 6.03%. При цене приватной продажи $0.1 и $0.005 инвесторы всё ещё в плюсе на 3.8x и 75x соответственно.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=940s (15:40)
  - Цитата автора: *«FIDA (Bonfida) and GMT (STEPN) were already down 97.9/90.5% while only having 10/6.03% of the supply in circulation. The price per token in the private sale was $0.1 (FIDA) and $0.005 (GMT), which means that the investors will still be selling at a profit (3.8x for FIDA and 75x for GMT).»*
  - Формулировка для менеджера: *«По утверждению автора видео: FIDA упала на 97.9% при 10% саплая в обороте, GMT — на 90.5% при 6.03%. При цене приватной продажи $0.1 и $0.005 инвесторы всё ещё в плюсе на 3.8x и 75x соответственно.»*
- **[UNVERIFIED]** FLOW 15.10.2021: открытие $17.68, минимум дня $9.2 (Kraken) и ~$6.1 (CoinList). Разлок 300M FLOW — 6x от circulating supply, потенциальное давление продаж до $5.1B. Инвесторы всё равно остались +100x.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1080s (18:00)
  - Цитата автора: *«On Oct. 15, 2021, FLOW opened the day at $17.68. By close, it traded at a low of $9.2 (Kraken) and ~$6.1 (CoinList). A maximum of $5.1B in selling pressure could've come through as 300M FLOW (6x the circulating supply) tokens were unlocked... investors were still up over 100x and could have continued selling in profit despite a 48% correction.»*
  - Формулировка для менеджера: *«По утверждению автора видео: FLOW 15.10.2021: открытие $17.68, минимум дня $9.2 (Kraken) и ~$6.1 (CoinList). Разлок 300M FLOW — 6x от circulating supply, потенциальное давление продаж до $5.1B. Инвесторы всё равно остались +100x.»*
- **[UNVERIFIED]** Radix DLT 15.09.2021: circulating supply вырос с 1.89B до 9.6B (5x), вызвав флеш-крэш более -90%, после чего цена отскочила на +800% от минимума и достигла нового ATH $0.687 (+55x от лоу).
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1120s (18:40)
  - Цитата автора: *«Before the unlock on Sep. 15, 2021, the circulating supply was ~1.89B, which was then bumped to 9.6B (5x), resulting in a flash crash of over 90%. By the daily close, the price rebounded and was up 800% from the low. EXRD made a new ATH of $0.687 (up 55x from the low).»*
  - Формулировка для менеджера: *«По утверждению автора видео: Radix DLT 15.09.2021: circulating supply вырос с 1.89B до 9.6B (5x), вызвав флеш-крэш более -90%, после чего цена отскочила на +800% от минимума и достигла нового ATH $0.687 (+55x от лоу).»*
- **[UNVERIFIED]** Oasis Network объявил экосистемный фонд на $160M за два дня до расширения предложения на 133% (1.471B ROSE). Цена удвоилась перед анлоком и упала вдвое в последующие дни.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1180s (19:40)
  - Цитата автора: *«Oasis Network announced a $160M ecosystem fund two days before the supply was set to increase by 133% (1.471B ROSE)... In the case of Oasis, unsurprisingly, the price more than doubled leading into the unlock, only to halve in the following days.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Oasis Network объявил экосистемный фонд на $160M за два дня до расширения предложения на 133% (1.471B ROSE). Цена удвоилась перед анлоком и упала вдвое в последующие дни.»*
- **[UNVERIFIED]** Nym объявил экосистемный фонд на $300M за день до анлока 80.75M NYM. Предложение выросло в 2.3x, цена упала более чем на 70% за девять дней.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1210s (20:10)
  - Цитата автора: *«Nym used the same playbook as Oasis, and announced a $300M ecosystem fund a day before the unlock... As the supply expanded by 2.3x, not only was the 'announcement pump' outdone, but the price fell by over 70% in 9 days.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Nym объявил экосистемный фонд на $300M за день до анлока 80.75M NYM. Предложение выросло в 2.3x, цена упала более чем на 70% за девять дней.»*
- **[UNVERIFIED]** Solana: аллокация community всего 1.6% саплая, цена продажи $0.04–$0.25, предложение должно было вырасти более чем в 7x. Вместо дампа — рост более 25,000% от ATL до ATH за счёт OTC-рынка с дисконтом 60–80% и кост-базой покупателей 2–4x.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1260s (21:00)
  - Цитата автора: *«SAFTs for Solana were being sold OTC anywhere from a 60-80% discount before the unlock. The fear was bought up by investors with higher conviction, resulting in their cost basis being 2-4x. There was a supply-side shock as less than 2% of tokens (community allocation) were actually in circulation.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Solana: аллокация community всего 1.6% саплая, цена продажи $0.04–$0.25, предложение должно было вырасти более чем в 7x. Вместо дампа — рост более 25,000% от ATL до ATH за счёт OTC-рынка с дисконтом 60–80% и кост-базой покупателей 2–4x.»*
- **[UNVERIFIED]** ICP: перпы запущены за 5 дней до спота, инвесторы ~37% саплая, команда ~62%, community ~1%. Цены входа $0.035 (seed), $0.63 (strategic), $4.17 (presale). ATH $2,831 (Binance) / $630 (Coinbase) — апсайд 151x–18,000x. OI $170M при экстремально отрицательном фандинге против аллокации инвесторов ~$110B.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1320s (22:00)
  - Цитата автора: *«Introducing perpetual futures days before launch allowed investors to hedge their positions and lock in a strong exit price. The $170M in OI coupled with extreme negative funding rates help substantiate the claim... The lack of required liquidity prevented these entities from fully hedging their locked tokens, but they were able to secure decent profits on partial positions.»*
  - Формулировка для менеджера: *«По утверждению автора видео: ICP: перпы запущены за 5 дней до спота, инвесторы ~37% саплая, команда ~62%, community ~1%. Цены входа $0.035 (seed), $0.63 (strategic), $4.17 (presale). ATH $2,831 (Binance) / $630 (Coinbase) — апсайд 151x–18,000x. OI $170M при экстремально отрицательном фандинге против аллокации инвесторов ~$110B.»*
- **[UNVERIFIED]** OXY: инвесторы были +110x, их 1B токенов стоили более $4B, но OI на контракте никогда не превышал $14.4M. Даунтренд вызван не хеджем, а отсутствием инкрементальных покупателей и фиксацией прибыли.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1380s (23:00)
  - Цитата автора: *«Investors were up about 110x at the highs. Their 1B tokens were worth over $4B. Yet, the OI on the contract never exceeded $14.4M... It stands to reason that the downtrend was not induced from hedging, but rather a lack of incremental buyers (due to the price appreciation, lack of utility, inflation schedule, price action, etc.) coupled with profit-taking.»*
  - Формулировка для менеджера: *«По утверждению автора видео: OXY: инвесторы были +110x, их 1B токенов стоили более $4B, но OI на контракте никогда не превышал $14.4M. Даунтренд вызван не хеджем, а отсутствием инкрементальных покупателей и фиксацией прибыли.»*
- **[UNVERIFIED]** AXS 25.10.2022: OI вырос до $193M за день до анлока при агрессивно отрицательном фандинге, затем откатился к пред-анлоковым уровням, а цена выросла почти на 19%. Это unwind хеджей, а не реальный спрос.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1420s (23:40)
  - Цитата автора: *«A week before the unlock, OI started skyrocketing, with average funding rates getting aggressively negative. The OI peaked at $193M a day before the unlock and then proceeded to unwind to pre-unlock levels. Simultaneously, the price rose by almost 19%.»*
  - Формулировка для менеджера: *«По утверждению автора видео: AXS 25.10.2022: OI вырос до $193M за день до анлока при агрессивно отрицательном фандинге, затем откатился к пред-анлоковым уровням, а цена выросла почти на 19%. Это unwind хеджей, а не реальный спрос.»*
- **[UNVERIFIED]** APE: ~77.3% разблокированных токенов принадлежали инвесторам. За 3 дня до анлока цена -20%, OI $117M. В день анлока OI упал до $84M, фандинг ушёл в минус, после чего APE прибавил более 40%.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1450s (24:10)
  - Цитата автора: *«~77.3% of the unlocked tokens belonged to the investors and the rest to the treasury. Three days before the unlock, APE fell by over 20%. The OI at the time was $117M. On the unlock day, OI dropped to $84M, and funding started turning negative... Moments after the unlock, OI started picking up, and APE followed suit by appreciating over 40%.»*
  - Формулировка для менеджера: *«По утверждению автора видео: APE: ~77.3% разблокированных токенов принадлежали инвесторам. За 3 дня до анлока цена -20%, OI $117M. В день анлока OI упал до $84M, фандинг ушёл в минус, после чего APE прибавил более 40%.»*
- **[UNVERIFIED]** Доступная ликвидность определяет, будет ли анлок «бычьим» или «медвежьим». При достаточной ликвидности анлоки дают рост, но это лишь отыгранная заранее версия медвежьего анлока. При недостатке ликвидности заблокированные токены не хеджируются полностью и продаются при разблокировке, создавая постоянный даунтренд.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1480s (24:40)
  - Цитата автора: *«Ample liquidity allows 'bullish unlocks' to transpire, although they are merely the priced-in versions of 'bearish unlocks'. A lack of liquidity disallows 'bullish unlocks', as locked tokens are not fully-hedged and will be sold when unlocked. These assets still experience a perpetual downtrend thanks to the absence of incremental buyers.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Доступная ликвидность определяет, будет ли анлок «бычьим» или «медвежьим». При достаточной ликвидности анлоки дают рост, но это лишь отыгранная заранее версия медвежьего анлока. При недостатке ликвидности заблокированные токены не хеджируются полностью и продаются при разблокировке, создавая постоянный даунтренд.»*
- **[UNVERIFIED]** Автор предлагает заменить time-based unlocks на milestone-based, привязав разблокировку к метрикам проекта (объём, TVL, пользователи). Это не святой грааль, но заставляет команду и инвесторов что-то сделать до получения токенов.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1560s (26:00)
  - Цитата автора: *«One way of doing this would be by opting for milestone-based unlocks instead of time-based unlocks... it does force the team and investors to deliver before receiving their tokens. Delivering a working product would bring in more users and, by extension, more demand. This could potentially translate into a reduced impact from a token unlock. Though this solution is far from the holy grail, it would be difficult to imagine where this structure doesn't fare better than the current structure.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Автор предлагает заменить time-based unlocks на milestone-based, привязав разблокировку к метрикам проекта (объём, TVL, пользователи). Это не святой грааль, но заставляет команду и инвесторов что-то сделать до получения токенов.»*
- **[UNVERIFIED]** По мере созревания индустрии анлоки могут перестать оказывать драматическое влияние на цену, так как разводнение будет закладываться в модели оценки.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=1620s (27:00)
  - Цитата автора: *«As the industry matures, teams start to figure out what makes a good token and the market becomes more efficient. We believe token unlocks could stop having such dramatic impacts on price, as dilution will be factored into pricing/valuation models.»*
  - Формулировка для менеджера: *«По утверждению автора видео: По мере созревания индустрии анлоки могут перестать оказывать драматическое влияние на цену, так как разводнение будет закладываться в модели оценки.»*
- **[UNVERIFIED]** Бесплатного обеда не существует: каждое обещание бесплатных денег (доходности) несёт риск, и часто риск значительно перевешивает потенциальную награду.
  - Ссылка/Якорь: https://members.delphidigital.io/reports/the-curious-case-of-token-unlocks&t=780s (13:00)
  - Цитата автора: *«TL;DR: There is no free lunch. Every promise of free money (yield) comes with risk. Often, the risk far outweighs the potential reward.»*
  - Формулировка для менеджера: *«По утверждению автора видео: Бесплатного обеда не существует: каждое обещание бесплатных денег (доходности) несёт риск, и часто риск значительно перевешивает потенциальную награду.»*


### Риски, ограничения и технические упрощения автора
- Риск ликвидности при выходе: физический размер пула ограничивает объём вывода. При пуле $100k USDT держатель всего саплая выведет максимум $100k, уничтожив цену. Это не рыночный риск, а структурный предел.
- Риск неполного хеджа: инсайдеры не могут захеджировать заблокированные токены в полном объёме. На ICP OI $170M против $110B аллокации (~0.15%), на OXY OI $14.4M против $4B (~0.36%). Непокрытая часть гарантированно выходит на спот при анлоке.
- Риск смены знака фандинга: отрицательный фандинг перед анлоком может развернуться, что ломает логику шорта на анлок и вызывает вынужденное закрытие позиций.
- Риск Short Squeeze: при «бычьем анлоке» (AXS +19%, APE +40%) шортисты закрываются по рынку, усиливая памп против их позиции.
- Риск lock-up в стейкинге: запертый стейкер не может выйти при плохих новостях. User A выходит на -80% с двойным количеством обесцененных токенов, тогда как User B продал на -60%.
- Риск разводнения через стейкинг-реварды: заблокированные токены инсайдеров стейкаются и получают пропорциональную долю эмиссии. На Aptos это 798M+ APT против 23.4M APT для community — доля ритейла постоянно размывается.
- Риск governance-фасада: контроль большинства застейканного саплая превращает голосование в формальность. Автор прямо называет governance rights «фасадом».
- Риск контрагента и биржи: перп-хедж и OTC-разгрузка зависят от конкретной площадки, её OI, стакана L2/L3 и способности исполнить крупный ордер без проскальзывания.
- Риск неопределённости намерений: невозможно фактически доказать, были ли announcement pump у Oasis и Nym умышленным созданием exit liquidity. Автор честно фиксирует это как подозрение на основе тайминга, а не как доказанный факт.
- Ограничение модели: отчёт построен на данных цикла 2021–2022. Автор сам отмечает, что по мере созревания рынка анлоки могут перестать оказывать драматическое влияние, так как разводнение будет закладываться в модели оценки.
- Ограничение решения: milestone-based unlocks не являются «святым граалем». При низкой ликвидности или при сохранении проклятия Low Float / High FDV влияние анлока не изменится — изменится лишь момент, когда команда получит токены.

### Кликабельные таймкоды ключевых моментов
- **SEC-01 | Введение**: [[[]Asset Management...
- **SEC-02 | The Curious Case of Token Unlocks**: DEC 02, 2022 [ • 24 Min Read ]

[[Priyansh Patel]]The authors have not purchased or sold a...
- **SEC-03 | Understanding the Basics**: The gold standard of a successful project is one with a useful, viable product and well-de...
- **SEC-04 | Risk/Reward Profile Associated With Staking**: Numerous projects offer additional tokens as a reward for staking (disregarding validator...
- **SEC-05 | Fully Diluted Valuations Matter**: It is a common theme among crypto participants that fully diluted valuations are irrelevan...
- **SEC-06 | Market Dynamics That Affect an Unlock**: Solana ecosystem tokens were notorious for having low floats. But the low market cap, high...
- **SEC-07 | Conclusion**: Tokens are an integral part of crypto projects. Over the years, the way token economies ar...


---

## 🎯 СЛОЙ 3: СОЦИАЛЬНАЯ ИНЖЕНЕРИЯ, ПСИХОЛОГИЯ КЛИЕНТА И ЗАКРЫТИЕ (SALES PSYCHOLOGY)

### Типичные ошибки и заблуждения розничных трейдеров
- МИФ: «FDV не имеет значения, важна только капитализация». Реальность: FDV — это метрика предложения, MC — метрика спроса. Их отношение показывает, во сколько раз рынку нужно увеличить спрос, чтобы удержать цену. FIDA -97.9% при 10% саплая в обороте и GMT -90.5% при 6.03% — прямое опровержение.
- МИФ: «Инвесторы не будут продавать в убыток». Реальность: инвестор с себестоимостью $0.005 (GMT) продаёт и на -90%, потому что он всё ещё +75x. Себестоимость инсайдера, а не текущая доходность, определяет его готовность продавать.
- МИФ: «Высокий APY на стейкинге — это пассивный доход». Реальность: доходность выплачивается в том же токене, который вы сами размываете. При падении цены с $1 до $0.3 двойное количество токенов даёт $60 вместо $100. Это не доход, а короткая позиция на собственный актив.
- МИФ: «Если токен застейкан, он не влияет на цену». Реальность: заблокированные и разблокированные токены одинаково стейкаются и получают реварды. На Aptos community владеет лишь 2.85% застейканного саплая, а 798M+ APT уходит стейкхолдерам — governance превращается в фасад.
- МИФ: «Анлок — это событие дня X». Реальность: анлок — процесс. На AXS цена начала отставать от рынка задолго до даты, OI раздулся за неделю, фандинг ушёл в минус. На APE цена упала на 20% за 3 дня до анлока.
- МИФ: «Рост цены после анлока = бычий анлок = спрос». Реальность: это unwind хеджей. Хеджеры разворачивают фьючерсы и одновременно продают спот, шортисты-спекулянты вынуждены закрываться — отсюда +19% на AXS и +40% на APE.
- МИФ: «Экосистемный фонд — это бычья новость». Реальность: Oasis объявил $160M за 2 дня до расширения предложения на 133%, Nym — $300M за день до анлока. Цена разгонялась, чтобы дать продавцам ликвидность, затем падала на 50–70%.
- МИФ: «OTC-дисконт — это бесплатный апсайд». Реальность: Solana — исключение, а не правило. Там был живой OTC-рынок и <2% саплая в обороте. В общем случае дисконт — это цена риска, который покупатель не видит: отсутствие хеджа и отсутствие ликвидности для выхода.
- МИФ: «Можно просто шортить всё, что разлокается, как GCR». Реальность: GCR шортил в конкретном режиме конца цикла при сжатой ликвидности. Тот же шорт на SOL в 2021-м был бы уничтожен ростом на 25,000%. Направленный шорт на анлок — ставка на отсутствие ликвидности, а не математическое преимущество.
- МИФ: «Документация проекта — это прозрачность». Реальность: LooksRare и Aptos не обманывали никого, вся информация была публичной. Но запутанный дизайн токеномики делает реальное распределение нечитаемым для среднего держателя — и это работает до тех пор, пока люди не разберутся, после чего доверие уже не восстановить.

### Вопросы клиентов и ответы (перехват авторитета и социальная инженерия)
### Вопрос 1: Я нашёл токен с APY 100% на стейкинге и ценой на историческом дне. Почему бы просто не зайти и не получать пассивный доход?
**Ответ:** Давайте разберём, что вам на самом деле платят. Доходность в 100% выплачивается не деньгами, а новыми токенами того же проекта — то есть вы финансируете собственную дилюцию. Стейкаете $100 в XYZ по $1, получаете 100 токенов, через год у вас 200 XYZ. Но если цена ушла на $0.3, у вас $60 вместо $100. Вы потеряли 40%, при том что «удвоили количество». Именно на этом рынок выпотрошили в DeFi Summer — люди не считали влияние цены на накопленную доходность. Теперь сантехника. Во-первых, эмиссия — это не доход, это новые токены из воздуха, которые продаются в тот же тонкий стакан. Во-вторых, есть физический предел выхода: если в пуле $100k USDT, а саплай 200k XYZ, вывести смогут только первые продавцы — дальше начинается race to the exits, и цена уничтожается. В-третьих, у стейкинга почти всегда есть lock-up. Пока вы заперты, свободный держатель продаёт на -60%; вы выходите на -80% с двойным количеством обесцененных токенов. Вы не получаете доход — вы держите короткую позицию на собственный актив с отрицательным математическим ожиданием. Институционалы не покупают APY. Они продают волатильность и собирают структурную премию там, где она считается математически: базис, ставка финансирования, межбиржевой спред. Это разные вселенные.

### Вопрос 2: Я слышал, что FDV — это фикция, важна только капитализация. Все нормальные люди так считают.
**Ответ:** Это самое дорогое заблуждение в крипте. Смотрите: капитализация — это метрика текущего спроса. FDV — метрика будущего предложения. Их отношение — это множитель, на который вырастет предложение. Если FDV/MC = 20, рынку нужно увеличить публичный спрос в 20 раз, чтобы цена просто осталась на месте. Не выросла — осталась. Теперь факты. FIDA упала на 97.9%, имея всего 10% саплая в обороте. GMT — на 90.5% при 6.03% в обороте. И при этом инвесторы приватных раундов всё ещё в плюсе: 3.8x по FIDA при цене входа $0.1 и 75x по GMT при $0.005. Они будут продавать и на -95%, потому что их себестоимость в 20–100 раз ниже вашей. Механика плейбука выглядит так: проект рейзит $10M при оценке $200M, инвестор получает токен по $0.05. На листинг выходит 1% саплая, публичный спрос $20M — капитализация $20M, но FDV $2B, цена $0.5, инвестор уже +10x. Приток $180M спекулятивного спроса разгоняет FDV до $20B, цена $5, инвестор +100x. Через 6 месяцев клфф заканчивается, и за следующие 12 месяцев предложение вырастает в 100 раз. Инвестор продаёт непрерывно даже после -80%, потому что он всё ещё +20x. Команда с 30% аллокацией при той же цене держит $1.2B. Вы не можете конкурировать с нулевой себестоимостью — это структурное, а не интеллектуальное преимущество. Поэтому вопрос не в том, кто победит в этой игре. Вопрос в том, зачем вообще в неё играть, когда рядом есть неэффективности, которые считаются математически.

### Вопрос 3: Но ведь некоторые анлоки дают рост — AXS прибавил 19%, APE 40% после разлока. Значит, можно просто покупать перед анлоком?
**Ответ:** Вы видите рост и читаете его как спрос. На самом деле вы видите unwind хеджей. Разберём AXS. 25 октября 2022 года на рынок должно было выйти ~21.5M токенов на $273M. За неделю до анлока открытый интерес начал взлетать, а средний фандинг ушёл агрессивно в минус. OI достиг $193M за день до разлока — это хеджеры шортанули перпы против заблокированного спота, чтобы зафиксировать цену выхода. В день анлока они получили токены, развернули фьючерсы и одновременно продали спот. Спекулянты, которые шортили в ожидании дампа, оказались вынуждены закрываться — их вынос и дал +19%. С APE то же самое: за 3 дня до анлока цена упала на 20%, OI был $117M, в день разлока упал до $84M, фандинг флипнулся в минус. Сразу после анлока OI начал расти, а APE прибавил более 40%. Подписи на CVD спота и перпов Binance подтверждают: это одновременный разворот фьючерсов и продажа спота. То есть «бычий анлок» — это не бычий анлок. Это медвежий анлок, который отыграли заранее, а в день X вы наблюдаете технический разворот хеджей. Покупать в этот момент — значит покупать у хеджера, который разгружает позицию. Направленная игра на анлоках — это казино с отрицательным EV, где вы платите за то, чтобы быть выходом для профессионала. Мы не берём направление. Мы берём структурную премию: фандинг, базис, спреды между площадками — там, где результат определяется математикой, а не нарративом.

### Вопрос 4: У меня $200k+ и доступ к OTC. Я могу купить SAFT с дисконтом 60–80%, как это делали на Solana. Зачем мне ваша инфраструктура?
**Ответ:** Solana — это исключение, которое вы принимаете за правило. Там действительно был живой OTC-рынок: SAFT торговались с дисконтом 60–80% до анлока, страх выкупался фондами с высокой conviction, их кост-база стала 2–4x, а в свободном обращении оставалось меньше 2% саплая. Это дало рефлексивный up-only и рост более 25,000% от ATL до ATH. Но посмотрите на остальные кейсы. OXY: инвесторы были +110x, их 1B токенов стоили больше $4B — а открытый интерес на контракте никогда не превышал $14.4M. Покрытие хеджа — около 0.36%. ICP: перпы запустили за 5 дней до спота, OI составил $170M при инвесторской аллокации, оценённой в $110B. Покрытие — около 0.15%. То есть даже профессионалы физически не могут захеджировать свои позиции, потому что нужной ликвидности не существует. Ваша реальная экспозиция — это не цена входа, а ликвидность выхода. Если в пуле $100k, вы не выведете $4B, сколько бы красиво ни выглядел ваш дисконт. Дисконт на OTC — это не бесплатный апсайд, это цена риска, который вы не видите: отсутствие хеджа, отсутствие выхода, вестинг-график, который вы не контролируете. У вас есть капитал, но нет инструмента управления этим риском. Дельта-нейтральная структура плюс мониторинг фандинга и спредов — это способ извлекать доход из той же самой неэффективности, но без направленной ставки на то, что кто-то другой купит вашу exit liquidity.

### Вопрос 5: Все эти анлоки — это же просто шорт. Почему бы не шортить всё, что разлокается, как делал GCR?
**Ответ:** GCR шортил в конкретном режиме рынка — конец цикла, когда ликвидность сжималась и покупателей не оставалось. Это была ставка на режим, а не на анлок. Проверьте на истории: тот же шорт на SOL в 2021-м был бы уничтожен ростом более чем на 25,000% от ATL до ATH. Направленный шорт на анлок — это ставка на то, что ликвидности не хватит. Иногда её хватает: OTC-дески, экосистемные фонды, announcement pump. Oasis объявил фонд на $160M за два дня до расширения предложения на 133% — цена удвоилась перед анлоком и упала вдвое после. Nym объявил $300M за день до разлока — цена рухнула на 70% за девять дней. Если бы вы шортили в момент объявления, вас бы вынесло на пампе до того, как вы дожили до дампа. Теперь анатомия. Анлок — это не сигнал, это набор переменных: размер разлока относительно саплая, доля инвесторов и команды, глубина стакана L2/L3, открытый интерес и ставка фандинга, наличие OTC-канала. FLOW: 300M токенов, шесть крат от circulating supply, потенциальное давление до $5.1B — цена упала на 48–65%, но инвесторы всё равно остались +100x. Radix: предложение выросло в 5 раз, флеш-крэш более -90%, а затем отскок +800% от минимума и новый ATH. Шорт без хеджа — это та же рулетка, просто с другой стороны стола. Мы не берём направление. Мы берём структурную премию: фандинг, базис, межбиржевой спред. Там, где результат определяется математикой, а не нарративом и не таймингом.



### Вопросы для самопроверки менеджера
1. Можешь ли ты объяснить клиенту разницу между FDV как метрикой предложения и MC как метрикой спроса, не используя слово «оценка»?
1. Сколько раз ты назвал клиенту конкретную доходность или гарантию? Если хоть раз — ты нарушил границы продукта.
1. Можешь ли ты на пальцах показать, почему инвестор с себестоимостью $0.005 продаёт на -90% и остаётся в плюсе 75x?
1. Как ты объяснишь «бычий анлок» AXS или APE, не скажешь «рынок передумал» и не скажешь «спрос вырос»?
1. Почему Solana — исключение, а не правило, и что именно сделало её исключением?
1. Что произойдёт с твоим клиентом, если он зайдёт в стейкинг с 100% APY и ценой на историческом дне? Опиши три механизма потерь.
1. Можешь ли ты объяснить, почему заблокированные токены инсайдеров всё равно получают стейкинг-реварды и как это размывает долю ритейла?
1. Как ты ответишь клиенту, который говорит: «У меня доступ к OTC, я куплю с дисконтом 70%»?
1. Почему шорт на анлок — это не арбитраж, а направленная ставка? В чём разница в терминах риска?
1. Сможешь ли ты удержаться от соблазна назвать конкретный APY, latency или комиссию, когда клиент будет настаивать на цифрах?
1. Как ты переведёшь разговор от «какой токен купить» к «как извлекать структурную премию без направленного риска»?
1. Что ты сделаешь, если клиент уже держит Low Float / High FDV токен с FDV/MC = 30 и ждёт анлока через месяц?

---

## ⚙️ СЛОЙ 4: ПРИКЛАДНОЙ СЛОЙ (Связь с NULLSPREAD & Product Application)
ПРИКЛАДНОЙ СЛОЙ NULLSPREAD (строго обособленный блок).

1) СПРЕДЫ, ИЗОЛИРОВАННЫЕ НОДЫ, ФРАГМЕНТАЦИЯ → блок B/02 (премия нод F/01–F/03).
Отчёт Delphi показывает, что ликвидность фрагментирована и асимметрична: один и тот же актив торгуется на споте, в перпах, на OTC-десках и на разных биржах по разным ценам. AXS и APE демонстрируют расхождение между спотовым и фьючерсным рынком в момент unwind хеджей; ICP — расхождение ATH между Binance ($2,831) и Coinbase ($630). Именно на таких расхождениях строится премия нод F/01–F/03: изолированные ноды снимают данные с разных площадок, а блок B/02 агрегирует спреды. Это не направленная ставка на анлок — это сбор структурной премии из фрагментации, которая в отчёте описана как постоянное свойство рынка.

2) ПРОСКАЛЬЗЫВАНИЕ, СТАКАН L2/L3, КОМИССИИ → блок C/03 (кейс на $2,200 и интерактивная PnL-модель).
Отчёт даёт прямую количественную основу: Liquidity Ceiling — при пуле $100k USDT держатель всего саплая выведет максимум $100k; OXY — OI $14.4M против позиции $4B (покрытие 0.36%); ICP — OI $170M против $110B (покрытие 0.15%). Это ровно тот класс риска, который моделирует блок C/03: глубина стакана L2/L3, проскальзывание при ребалансировке и экстренном закрытии, комиссии. Интерактивная PnL-модель позволяет клиенту увидеть на цифрах, что произойдёт с его позицией при выходе в тонком пуле — до того, как он это испытает на реальном капитале.

3) РИСКИ, ДЕПЕГ, ЛИКВИДАЦИИ → Меморандум о рисках (R/01–R/04).
Отчёт фиксирует четыре риска, напрямую ложащихся в меморандум: (а) риск ликвидности выхода — физический предел пула; (б) риск неполного хеджа — инсайдеры не могут закрыть всю позицию, непокрытая часть выходит на спот; (в) риск смены знака фандинга — отрицательный фандинг перед анлоком может развернуться и сломать логику позиции; (г) риск Short Squeeze — при «бычьем анлоке» шортисты закрываются по рынку, усиливая движение против них. Плюс риск контрагента и биржи: перп-хедж и OTC-разгрузка зависят от конкретной площадки. Всё это — границы применимости дельта-нейтральной структуры, зафиксированные в CLAIM-002.

4) РИСОВАННЫЕ ОБЪЁМЫ (WASH TRADING) → Принцип трёх площадок (M/01).
Отчёт показывает, что объём и OI легко искажаются: announcement pump у Oasis и Nym создавал видимость спроса перед анлоком; OI на AXS раздулся до $193M и схлопнулся к пред-анлоковым уровням; на OXY OI никогда не превышал $14.4M при позиции в $4B. Один источник данных не даёт картины. Принцип трёх площадок (M/01) требует перекрёстной верификации объёма, OI и фандинга минимум по трём независимым источникам, чтобы отличить реальный поток от нарисованного.

ОГРАНИЧЕНИЯ И ГРАНИЦЫ:
— Отчёт Delphi — это рыночная аналитика, а не подтверждение продуктовых метрик NULLSPREAD. Никакие цифры из отчёта не могут использоваться как обещание доходности.
— Конкретный APY, latency и комиссионная сетка NULLSPREAD остаются в статусе UNVERIFIED (CLAIM-003). Запрещено называть клиенту любые точные цифры годовых, микросекундные задержки или тарифы.
— Дельта-нейтральность устраняет направленный ценовой риск, но не устраняет риск ликвидации короткой позиции при резком пампе, риск смены знака фандинга, риск проскальзывания при ребалансировке и риск биржи (CLAIM-002).
— Платформа не гарантирует постоянного наличия арбитражных возможностей: они зависят от волатильности и ликвидности внешних рынков (CLAIM-001).
— Прямая продуктовая связь по разделу о milestone-based unlocks не установлена (общетехнический фундамент рынка).
