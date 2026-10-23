"""Roleplay sparring simulator: Skeptical Crypto Investor vs Manager."""

from __future__ import annotations

import random
from typing import Dict, List, Optional
from research_academy.academy.evaluation import AnswerEvaluator
from research_academy.academy.question_generator import QuestionGenerator
from research_academy.database import Database
from research_academy.models import AcademyQuestion, EvaluationResult


class InvestorPersona:
    def __init__(
        self,
        name: str = "Виктор Сергеевич",
        age: int = 42,
        deposit_usd: int = 50000,
        exchange: str = "Bybit",
        trading_style: str = "Торгует фьючерсы BTC/ETH, разбирается в стакане, фандинге и проскальзывании",
        difficulty: str = "hard",
    ):
        self.name = name
        self.age = age
        self.deposit_usd = deposit_usd
        self.exchange = exchange
        self.trading_style = trading_style
        self.difficulty = difficulty

    def intro_prompt(self) -> str:
        return (
            f"Клиент: {self.name}, {self.age} года.\n"
            f"Депозит: ${self.deposit_usd:,} (биржа {self.exchange}).\n"
            f"Профиль: {self.trading_style}.\n"
            f"Уровень сложности: {self.difficulty.upper()}.\n"
            f"Настроение: скептичное, требует точных технических формулировок, ловит на общих фразах."
        )


class RoleplaySession:
    def __init__(
        self,
        db: Database,
        difficulty: str = "hard",
        persona: Optional[InvestorPersona] = None,
    ):
        self.db = db
        self.persona = persona or InvestorPersona(difficulty=difficulty)
        self.q_gen = QuestionGenerator(db)
        self.evaluator = AnswerEvaluator()
        self.questions = self.q_gen.get_all_questions()
        self.history: List[Dict[str, str]] = []

    def get_challenge(self, index: int = 0) -> AcademyQuestion:
        idx = index % len(self.questions)
        return self.questions[idx]

    def submit_response(
        self, question: AcademyQuestion, manager_answer: str
    ) -> EvaluationResult:
        result = self.evaluator.evaluate_response(question, manager_answer)
        self.history.append({
            "question": question.question,
            "answer": manager_answer,
            "score": str(result.score),
            "passing": str(result.is_passing),
            "critical_error": str(result.has_critical_error),
        })
        return result

