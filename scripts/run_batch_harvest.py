import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from research_academy.config import get_config
from research_academy.database import Database
from research_academy.domain.manager import DomainManager
from research_academy.pipeline.matrix_harvester import MatrixHarvester
from research_academy.pipeline.web_harvester import WebHarvester

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("batch_harvest")

def main():
    config = get_config()
    db = Database(config.database_path)
    manager = DomainManager(config.project_root)

    # 1. YouTube Harvest for missing modules (04, 05, 06)
    yt_harvester = MatrixHarvester(config=config, db=db)
    yt_modules = ["04_onchain_logistics", "05_risk_and_hedging", "06_quant_stack_and_mindset"]

    for mod in yt_modules:
        logger.info(f"=== Starting YouTube harvest for {mod} ===")
        res = yt_harvester.harvest_module(mod)
        logger.info(f"=== Completed YouTube {mod}: {len(res)} videos ===")

    # 2. Web Harvest across all modules 00 through 06
    web_harvester = WebHarvester(config=config, db=db, domain_manager=manager)
    topics = [
        "00_crypto_fundamentals",
        "01_market_structure",
        "02_arbitrage_and_derivatives",
        "03_orderbook_mechanics",
        "04_onchain_logistics",
        "05_risk_and_hedging",
        "06_quant_stack_and_mindset",
    ]

    for topic_id in topics:
        logger.info(f"=== Starting Web harvest for topic {topic_id} ===")
        try:
            sources = web_harvester.harvest_topic(topic_id=topic_id, domain="crypto", max_results=4)
            logger.info(f"=== Completed Web harvest for {topic_id}: {len(sources)} sources ===")
        except Exception as e:
            logger.error(f"Error harvesting web for {topic_id}: {e}")

    logger.info("BATCH HARVEST COMPLETE!")

if __name__ == "__main__":
    main()

