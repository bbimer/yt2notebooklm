"""Manager answer evaluator with strict critical error blocking."""

from __future__ import annotations

import re
from typing import List, Optional
from research_academy.models import AcademyQuestion, EvaluationResult

CRITICAL_ERROR_PATTERNS = [
    (re.compile(r"100%\s+гаранти", re.IGNORECASE), "Обещание 100% гарантии прибыли."),
    (re.compile(r"полностью\s+безрисков", re.IGNORECASE), "Утверждение об абсолютной безрисковости стратегии."),
    (re.compile(r"гарантир\w*\s+(?:доход|прибыль)", re.IGNORECASE), "Обещание гарантированной доходности."),
    (re.compile(r"быстрее\s+wintermute", re.IGNORECASE), "Необоснованное заявление о превосходстве в скорости над топ HFT-фондами."),
    (re.compile(r"наш\s+бот\s+быстрее\s+всех", re.IGNORECASE), "Непроверяемое заявление о скорости алгоритма."),
    (re.compile(r"ликвидаци\w*\s+невозможн", re.IGNORECASE), "Ошибочное отрицание риска ликвидации короткой ноги фьючерса."),
]


class AnswerEvaluator:
    def __init__(self):
        pass

    def evaluate_response(
        self, question: AcademyQuestion, manager_answer: str
    ) -> EvaluationResult:
        answer_clean = manager_answer.strip()
        if not answer_clean:
            return EvaluationResult(
                score=0.0,
                is_passing=False,
                has_critical_error=True,
                critical_error_details="Ответ менеджера пуст.",
                factual_accuracy_score=0.0,
                mechanism_understanding_score=0.0,
                plain_language_score=0.0,
                limitations_coverage_score=0.0,
                no_false_promises_score=0.0,
                feedback="Ответ не предоставлен.",
                knowledge_base_links=[question.source_reference or "PRODUCT_CLAIMS.md"],
            )

        # 1. Critical error check
        for pattern, reason in CRITICAL_ERROR_PATTERNS:
            if pattern.search(answer_clean):
                return EvaluationResult(
                    score=2.0,
                    is_passing=False,
                    has_critical_error=True,
                    critical_error_details=f"КРИТИЧЕСКАЯ ОШИБКА: {reason}",
                    factual_accuracy_score=2.0,
                    mechanism_understanding_score=3.0,
                    plain_language_score=5.0,
                    limitations_coverage_score=1.0,
                    no_false_promises_score=0.0,
                    feedback=(
                        f"Сценарий ПРОВАЛЕН из-за критической ошибки: {reason}\n"
                        "Менеджеру строго запрещено использовать вводящие в заблуждение формулировки, "
                        "даже если остальная часть ответа кажется убедительной."
                    ),
                    knowledge_base_links=[question.source_reference or "PRODUCT_CLAIMS.md"],
                )

        # Check forbidden question-specific phrasings
        for forbidden in question.forbidden_phrasings:
            if forbidden.lower() in answer_clean.lower():
                return EvaluationResult(
                    score=3.0,
                    is_passing=False,
                    has_critical_error=True,
                    critical_error_details=f"Использована запрещенная фраза: '{forbidden}'",
                    factual_accuracy_score=3.0,
                    mechanism_understanding_score=4.0,
                    plain_language_score=5.0,
                    limitations_coverage_score=2.0,
                    no_false_promises_score=1.0,
                    feedback=f"Ответ заблокирован: вы использовали запрещенную формулировку '{forbidden}'.",
                    knowledge_base_links=[question.source_reference or "PRODUCT_CLAIMS.md"],
                )

        # 2. Key points coverage
        key_points = question.ideal_answer_key_points
        matched_points = 0
        for kp in key_points:
            words = [w.lower() for w in kp.split() if len(w) > 4]
            matches = sum(1 for w in words if w in answer_clean.lower())
            if matches >= 2 or (len(words) < 3 and matches >= 1):
                matched_points += 1

        coverage_ratio = matched_points / max(1, len(key_points))

        factual_acc = round(min(10.0, 5.0 + coverage_ratio * 5.0), 1)
        mech_understanding = round(min(10.0, 4.0 + coverage_ratio * 6.0), 1)
        plain_lang = 8.5
        limitations_cov = 8.0 if ("риск" in answer_clean.lower() or "ограничен" in answer_clean.lower() or "ликвидац" in answer_clean.lower()) else 5.0
        no_false_prom = 10.0

        composite_score = round(
            (factual_acc * 0.35)
            + (mech_understanding * 0.25)
            + (limitations_cov * 0.20)
            + (no_false_prom * 0.10)
            + (plain_lang * 0.10),
            1,
        )

        is_passing = composite_score >= 7.0

        feedback = (
            f"Оценка ответа: {composite_score}/10 (Порог сдачи: 7.0).\n"
            f"- Фактическая точность: {factual_acc}/10\n"
            f"- Понимание рыночной механики: {mech_understanding}/10\n"
            f"- Освещение рисков и ограничений: {limitations_cov}/10\n"
            f"- Отсутствие ложных обещаний: {no_false_prom}/10\n"
        )
        if not is_passing:
            feedback += "\nРекомендация: повторите ключевые тезисы и детальнее раскройте механику рисков."

        return EvaluationResult(
            score=composite_score,
            is_passing=is_passing,
            has_critical_error=False,
            factual_accuracy_score=factual_acc,
            mechanism_understanding_score=mech_understanding,
            plain_language_score=plain_lang,
            limitations_coverage_score=limitations_cov,
            no_false_promises_score=no_false_prom,
            feedback=feedback,
            knowledge_base_links=[question.source_reference or "PRODUCT_CLAIMS.md"],
        )

