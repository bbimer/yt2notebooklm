"""Mock LLM Provider for unit testing and offline development."""

from __future__ import annotations

from typing import Optional
from research_academy.llm.base import LLMProvider
from research_academy.models import (
    ClaimModel,
    ClaimType,
    GatekeeperEvaluation,
    GatekeeperVerdict,
    MethodistAnalysis,
    VideoMetadata,
    VideoTranscript,
)


class MockLLMProvider(LLMProvider):
    def __init__(
        self,
        default_gatekeeper_decision: GatekeeperVerdict = GatekeeperVerdict.ACCEPT,
        default_gatekeeper_score: float = 8.5,
    ):
        self.default_decision = default_gatekeeper_decision
        self.default_score = default_gatekeeper_score

    def evaluate_gatekeeper(
        self, video: VideoMetadata, transcript: VideoTranscript
    ) -> GatekeeperEvaluation:
        # If title contains scam keywords, simulate rejection
        if "scam" in video.title.lower() or "1000x" in video.title.lower():
            return GatekeeperEvaluation(
                relevance_score=3.0,
                technical_depth_score=2.0,
                practical_value_score=2.0,
                source_quality_score=2.0,
                commercial_noise_score=9.0,
                confidence_score=0.95,
                decision=GatekeeperVerdict.REJECT,
                reasons=["High commercial noise", "Signal group promotion", "Zero technical depth"],
                uncertainties=[],
            )

        return GatekeeperEvaluation(
            relevance_score=self.default_score,
            technical_depth_score=self.default_score - 0.5,
            practical_value_score=self.default_score,
            source_quality_score=self.default_score,
            commercial_noise_score=2.0,
            confidence_score=0.9,
            decision=self.default_decision,
            reasons=[
                "High technical depth regarding market microstructure",
                "Clear explanations of order book queues and latency",
            ],
            uncertainties=["Exact CEX fee schedules vary by VIP tier"],
        )

    def generate_methodist_analysis(
        self,
        video: VideoMetadata,
        transcript: VideoTranscript,
        product_claims_text: Optional[str] = None,
    ) -> MethodistAnalysis:
        # Build timestamped claims based on actual transcript segments
        claims = []
        if transcript.segments:
            seg0 = transcript.segments[0]
            claims.append(
                ClaimModel(
                    claim_type=ClaimType.SOURCE_CLAIM,
                    statement="Funding rate arbitrage generates return by collecting periodic funding payments while maintaining zero delta.",
                    source_url=video.url,
                    timestamp_seconds=seg0.start_seconds,
                    timestamp_formatted=seg0.timestamp_formatted,
                    quote_text=seg0.text,
                    verification_status="verified",
                    allowed_sales_phrasing="Дельта-нейтральная стратегия позволяет получать ставку финансирования без направленного риска движения курса.",
                )
            )

        return MethodistAnalysis(
            summary=f"Детальный разбор стратегий и микроструктуры по теме {video.topic_id}.",
            key_concepts=[
                "Спот-фьючерсный базис (Spot-Perp Basis)",
                "Ставка финансирования (Funding Rate) и периоды начисления",
                "Лимиты маржинального обеспечения и риск шорт-сквиза",
            ],
            mechanisms_explanation="Одновременное открытие длинной позиции на спотовом рынке и эквивалентной короткой позиции на бессрочном фьючерсе. Риск цены устраняется взаимокомпенсацией дельты.",
            terminology_and_slang=[
                {"term": "Funding Rate", "definition_or_context": "Периодическая выплата между лонгами и шортами для удержания цены фьючерса к споту."},
                {"term": "Delta Neutral", "definition_or_context": "Состояние портфеля, при котором его суммарная чувствительность к цене базового актива равна нулю."},
            ],
            numerical_examples=[
                "Депозит $10,000: покупка $5,000 спот BTC + открытие шорт 1x фьючерс BTC на $5,000. При фандинге 0.01% за 8 часов доходность составляет $0.50 за такт."
            ],
            common_mistakes_and_myths=[
                "Заблуждение: Дельта-нейтральность означает 100% отсутствие любых рисков. Ошибка: игнорирование риска ликвидации шорта при росте актива."
            ],
            risks_and_limitations=[
                "Риск смены знака фандинга на отрицательный.",
                "Риск биржевого контрагента (CEX counterparty risk).",
                "Риск проскальзывания при экстренной ребалансировке.",
            ],
            client_questions_and_answers=[
                {
                    "question": "Почему вы не используете 10x плечо для увеличения прибыли от фандинга?",
                    "answer": "Высокое плечо многократно повышает риск ликвидации фьючерсной ноги при резком восходящем импульсе рынка, что разрушает дельта-нейтральность. Мы работаем с консервативным плечом 1x-2x.",
                },
                {
                    "question": "Что происходит, когда фандинг уходит в минус?",
                    "answer": "Если фандинг отрицателен более 2 циклов, позиция планово закрывается или ребалансируется в другие активы с положительной ставкой.",
                },
                {
                    "question": "Как защищен депозит на спотовой стороне?",
                    "answer": "Спотовая позиция не имеет кредитного плеча и риска ликвидации. Падение цены спота компенсируется прибылью от шорт-позиции.",
                },
                {
                    "question": "Чем ваша стратегия отличается от простого стейкинга?",
                    "answer": "Стейкинг несет 100% рыночный риск просадки цены базовой монеты. Арбитраж фандинга устраняет ценовой риск монеты через дельта-хедж.",
                },
                {
                    "question": "Гарантируете ли вы фиксированный доход в месяц?",
                    "answer": "Нет, фиксированных гарантий на рынке нет. Доходность динамическая и зависит от рыночной волатильности и процентных ставок.",
                },
            ],
            self_check_questions=[
                "В каких условиях ставка финансирования становится отрицательной?",
                "Как рассчитывается ликвидационная цена шорт-позиции при наличии спотового обеспечения?",
            ],
            key_claims=claims,
            nullspread_connection="Материал подтверждает принципы дельта-нейтрального арбитража, зафиксированные в CLAIM-001 и CLAIM-002.",
        )

