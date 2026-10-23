"""Mock YouTube Provider for offline testing and demonstration mode."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from research_academy.models import VideoMetadata
from research_academy.providers.base import YouTubeProvider


class MockYouTubeProvider(YouTubeProvider):
    def __init__(self, sample_videos: Optional[List[VideoMetadata]] = None):
        self.sample_videos = sample_videos or self._default_mock_videos()

    def search(
        self,
        query: str,
        topic_id: str,
        max_results: int = 20,
    ) -> List[VideoMetadata]:
        matched = []
        for v in self.sample_videos:
            if topic_id == v.topic_id or query.lower() in v.title.lower():
                copy_v = v.model_copy()
                copy_v.queries_matched = [query]
                matched.append(copy_v)
        return matched[:max_results]

    def get_video_details(
        self,
        video_ids: List[str],
        topic_id: str = "general",
        query_matched: Optional[str] = None,
    ) -> List[VideoMetadata]:
        res = []
        for vid in video_ids:
            for v in self.sample_videos:
                if v.video_id == vid:
                    c = v.model_copy()
                    if query_matched:
                        c.queries_matched = [query_matched]
                    res.append(c)
        return res

    def _default_mock_videos(self) -> List[VideoMetadata]:
        now = datetime.now(timezone.utc)
        v1 = VideoMetadata(
            video_id="demo_fund_01",
            title="Understanding Crypto Funding Rate Arbitrage and Delta Neutral Hedging",
            description="Complete quantitative overview of spot-perp basis trade, funding payments, and liquidity management.",
            channel_id="chan_bellcurve",
            channel_title="Bell Curve Research",
            published_at=now,
            duration_seconds=1450,
            view_count=18400,
            like_count=980,
            channel_follower_count=45000,
            url="https://www.youtube.com/watch?v=demo_fund_01",
            topic_id="02_arbitrage_types",
            queries_matched=["funding rate arbitrage delta neutral strategy explained"],
            language="en",
        )
        v1.calculate_derived_metrics()

        v2 = VideoMetadata(
            video_id="demo_micro_02",
            title="Market Microstructure: Order Books, Matching Engines, and Slippage",
            description="Deep dive into maker-taker fees, queue priority, latency, and how market makers maintain spread.",
            channel_id="chan_wintermute",
            channel_title="Wintermute Engineering",
            published_at=now,
            duration_seconds=1820,
            view_count=24500,
            like_count=1450,
            channel_follower_count=12000,
            url="https://www.youtube.com/watch?v=demo_micro_02",
            topic_id="03_orderbook_mechanics",
            queries_matched=["order book mechanics bid ask spread depth explained"],
            language="en",
        )
        v2.calculate_derived_metrics()

        v3 = VideoMetadata(
            video_id="demo_scam_03",
            title="СДЕЛАЛ +500% НА АРБИТРАЖЕ! СИГНАЛЫ В ТЕЛЕГРАМ 1000x",
            description="Подпишись на t.me/pumpsignals1000x и забери бесплатная связка на 100% прибыль каждый день!",
            channel_id="chan_scam",
            channel_title="Crypto Easy Money",
            published_at=now,
            duration_seconds=300,  # 5 mins - too short
            view_count=50000,
            like_count=200,
            channel_follower_count=100000,
            url="https://www.youtube.com/watch?v=demo_scam_03",
            topic_id="02_arbitrage_types",
            queries_matched=["виды арбитража криптовалют межбиржевой внутрибиржевой"],
            language="ru",
        )
        v3.calculate_derived_metrics()

        return [v1, v2, v3]

