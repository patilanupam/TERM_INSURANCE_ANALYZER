"""
APScheduler-based periodic scraper.
Runs both scrapers every 24 hours and upserts results into the DB.
Also runs seed data on first startup if DB is empty.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, InsurancePlan
from scraper.seed_data import SEED_PLANS
from scraper.policybazaar import scrape_policybazaar
from scraper.insurancedekho import scrape_insurancedekho

logger = logging.getLogger(__name__)


def _upsert_plans(plans: list, db: Session):
    """Insert plans that don't already exist (matched by plan_name + provider)."""
    for p in plans:
        existing = (
            db.query(InsurancePlan)
            .filter(
                InsurancePlan.plan_name == p["plan_name"],
                InsurancePlan.provider == p["provider"],
            )
            .first()
        )
        if existing:
            for k, v in p.items():
                setattr(existing, k, v)
            existing.scraped_at = datetime.utcnow()
        else:
            db.add(InsurancePlan(**p))
    db.commit()


def run_scrape_job():
    """Full scrape job: tries live scraping, always ensures seed data exists."""
    db = SessionLocal()
    try:
        total = db.query(InsurancePlan).count()

        # Always seed if DB is empty
        if total == 0:
            logger.info("DB empty — seeding with fallback data")
            _upsert_plans(SEED_PLANS, db)

        # Try live scraping
        logger.info("Starting live scrape: PolicyBazaar...")
        pb_plans = scrape_policybazaar()
        if pb_plans:
            _upsert_plans(pb_plans, db)
            logger.info(f"Upserted {len(pb_plans)} PolicyBazaar plans")
        else:
            logger.info("PolicyBazaar returned no plans — using seed data only")

        logger.info("Starting live scrape: InsuranceDekho...")
        id_plans = scrape_insurancedekho()
        if id_plans:
            _upsert_plans(id_plans, db)
            logger.info(f"Upserted {len(id_plans)} InsuranceDekho plans")
        else:
            logger.info("InsuranceDekho returned no plans — using seed data only")

        final_count = db.query(InsurancePlan).count()
        logger.info(f"Scrape complete. Total plans in DB: {final_count}")

    except Exception as e:
        logger.error(f"Scrape job error: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start APScheduler background scheduler that runs scrape every 24 hours."""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scrape_job,
        trigger="interval",
        hours=24,
        id="scrape_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — scrape runs every 24 hours")
    return scheduler
