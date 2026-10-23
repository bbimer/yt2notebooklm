"""Tests for Stage 5: Sales Academy (Question Generator, Evaluator, Critical Error Blocking)."""

from pathlib import Path
import pytest
from research_academy.academy.evaluation import AnswerEvaluator
from research_academy.academy.question_generator import QuestionGenerator
from research_academy.academy.roleplay import InvestorPersona, RoleplaySession
from research_academy.database import Database
from research_academy.models import AcademyQuestion, QuestionCategory


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test.db"
    return Database(db_file)


def test_question_generator(temp_db: Database):
    q_gen = QuestionGenerator(temp_db)
    questions = q_gen.get_questions_by_topic("02_arbitrage_types", count=2)
    assert len(questions) <= 2
    for q in questions:
        assert q.topic_id == "02_arbitrage_types"
        assert len(q.ideal_answer_key_points) > 0

    # Test alias resolution
    aliased_questions = q_gen.get_questions_by_topic("funding-rate-arbitrage", count=1)
    assert len(aliased_questions) == 1
    assert aliased_questions[0].topic_id == "02_arbitrage_types"


def test_evaluator_critical_error_blocks_passing():
    evaluator = AnswerEvaluator()
    question = AcademyQuestion(
        id="Q-TEST",
        topic_id="funding-rate-arbitrage",
        category=QuestionCategory.TECHNICAL,
        question="Как работает дельта-нейтральный арбитраж?",
        ideal_answer_key_points=["Открытие спот и шорт фьючерс"],
    )

    # Manager answers with an invalid guarantee
    bad_answer = "Мы открываем спот и фьючерс, это дает 100% гарантию прибыли без всяких рисков."
    result = evaluator.evaluate_response(question, bad_answer)

    assert result.has_critical_error is True
    assert result.is_passing is False
    assert result.score <= 3.0
    assert "КРИТИЧЕСКАЯ ОШИБКА" in result.critical_error_details


def test_evaluator_valid_response_passes():
    evaluator = AnswerEvaluator()
    question = AcademyQuestion(
        id="Q-TEST",
        topic_id="funding-rate-arbitrage",
        category=QuestionCategory.TECHNICAL,
        question="Как работает дельта-нейтральный арбитраж?",
        ideal_answer_key_points=[
            "Одновременное открытие длинной позиции на споте и короткой позиции на фьючерсе",
            "Дельта равна нулю",
            "Доход формируется за счет получения ставки финансирования",
        ],
        forbidden_phrasings=["безрисковая стратегия"],
    )

    good_answer = (
        "Дельта-нейтральный арбитраж строится на одновременном открытии длинной позиции на споте "
        "и короткой позиции на бессрочном фьючерсе в равном объеме. Суммарная дельта равна нулю, "
        "поэтому рыночные колебания цены компенсируют друг друга. Доход формируется за счет получения "
        "ставки финансирования (funding rate). При этом сохраняется риск изменения фандинга и кредитный риск биржи."
    )
    result = evaluator.evaluate_response(question, good_answer)

    assert result.has_critical_error is False
    assert result.is_passing is True
    assert result.score >= 7.0


def test_roleplay_session(temp_db: Database):
    persona = InvestorPersona(name="Алексей", deposit_usd=100000, difficulty="hard")
    session = RoleplaySession(temp_db, persona=persona)

    challenge = session.get_challenge(0)
    assert challenge is not None

    answer = "Мы хеджируем спотовую позицию шортом на фьючерсах, дельта равна 0, получаем ставку финансирования."
    res = session.submit_response(challenge, answer)
    assert len(session.history) == 1
    assert float(session.history[0]["score"]) > 0.0

