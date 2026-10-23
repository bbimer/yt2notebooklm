"""Unit tests for OpenRouter LLM Provider and DeepSeek integration."""

from unittest.mock import MagicMock, patch
import pytest

from research_academy.llm.openrouter import OpenRouterLLMProvider, clean_json_payload
from research_academy.models import (
    GatekeeperVerdict,
    TranscriptSegment,
    VideoMetadata,
    VideoTranscript,
)


def test_clean_json_payload():
    assert clean_json_payload('{"a": 1}') == '{"a": 1}'
    assert clean_json_payload('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert clean_json_payload('```\n{"a": 1}\n```') == '{"a": 1}'


def test_openrouter_provider_init_requires_key():
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
        OpenRouterLLMProvider(api_key="")


@patch("research_academy.llm.openrouter.OpenAI")
def test_openrouter_evaluate_gatekeeper(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""{
                    "relevance_score": 9.0,
                    "technical_depth_score": 8.0,
                    "practical_value_score": 8.5,
                    "source_quality_score": 7.5,
                    "commercial_noise_score": 1.0,
                    "confidence_score": 0.9,
                    "decision": "ACCEPTED_CORE",
                    "reasons": ["[01:20] Solid matching engine explanation"],
                    "uncertainties": [],
                    "counter_evidence": ["Good intro"]
                }"""
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response

    provider = OpenRouterLLMProvider(api_key="test_key", model_name="deepseek/deepseek-v4.1-flash")
    video = VideoMetadata(
        video_id="test1234567",
        title="Matching Engine 101",
        url="https://www.youtube.com/watch?v=test1234567",
        channel_title="Crypto Academy",
        channel_id="chan1",
        topic_id="01_market_structure",
    )
    transcript = VideoTranscript(
        video_id="test1234567",
        language="en",
        segments=[
            TranscriptSegment(start_seconds=10.0, end_seconds=30.0, text="Matching engine takes orders.")
        ],
    )

    evaluation = provider.evaluate_gatekeeper(video, transcript)
    assert evaluation.relevance_score == 9.0
    assert evaluation.decision == GatekeeperVerdict.ACCEPT
    assert evaluation.composite_score is not None
    assert evaluation.composite_score >= 7.0


@patch("research_academy.llm.openrouter.OpenAI")
def test_openrouter_generate_methodist_analysis(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""{
                    "summary": "Summary of orderbook mechanics",
                    "key_concepts": ["Order Book", "Matching Engine"],
                    "mechanisms_explanation": "Limit vs Market orders",
                    "terminology_and_slang": [{"term": "Top of Book", "definition_or_context": "Best bid/ask"}],
                    "numerical_examples": ["10 BTC market order at 50,000"],
                    "common_mistakes_and_myths": ["Assuming no slippage"],
                    "risks_and_limitations": ["Slippage risk"],
                    "client_questions_and_answers": [{"question": "What is slippage?", "answer": "Execution difference."}],
                    "self_check_questions": ["How does L2 book work?"],
                    "key_claims": [
                        {
                            "claim_type": "source_claim",
                            "statement": "Matching engine executes orders deterministically.",
                            "timestamp_seconds": 15.0,
                            "timestamp_formatted": "00:15",
                            "quote_text": "Matching engine executes orders."
                        }
                    ],
                    "nullspread_connection": "Relevant to liquidity aggregation."
                }"""
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response

    provider = OpenRouterLLMProvider(api_key="test_key", model_name="deepseek/deepseek-v4.1-flash")
    video = VideoMetadata(
        video_id="vid_test_xyz",
        title="Matching Engine 101",
        url="https://www.youtube.com/watch?v=vid_test_xyz",
        channel_title="Crypto Academy",
        channel_id="chan1",
        topic_id="01_market_structure",
    )
    transcript = VideoTranscript(
        video_id="vid_test_xyz",
        language="en",
        segments=[
            TranscriptSegment(start_seconds=15.0, end_seconds=30.0, text="Matching engine executes orders.")
        ],
    )

    analysis = provider.generate_methodist_analysis(video, transcript)
    assert analysis.summary == "Summary of orderbook mechanics"
    assert len(analysis.key_claims) == 1
    # Check that source_url is populated from video_id
    assert analysis.key_claims[0].source_url == "https://www.youtube.com/watch?v=vid_test_xyz"
    assert analysis.key_claims[0].timestamp_formatted == "00:15"
