"""
APScheduler-based periodic scraper.
Priority: BankBazaar (live HTML) → seed data (fallback)
PolicyBazaar / InsuranceDekho kept as optional extras but are often blocked.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, InsurancePlan
from scraper.seed_data import SEED_PLANS
from scraper.bankbazaar import scrape_bankbazaar
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
    """
    Full scrape job:
    1. BankBazaar (primary — works reliably with requests)
    2. PolicyBazaar + InsuranceDekho (optional, often blocked)
    3. Seed data guaranteed as fallback if DB is empty
    """
    db = SessionLocal()
    try:
        total = db.query(InsurancePlan).count()

        # Seed fallback if DB completely empty
        if total == 0:
            logger.info("DB empty — seeding with fallback data")
            _upsert_plans(SEED_PLANS, db)

        # ── PRIMARY: BankBazaar (reliable, server-side HTML) ──
        logger.info("Starting live scrape: BankBazaar...")
        bb_plans = scrape_bankbazaar()
        if bb_plans:
            _upsert_plans(bb_plans, db)
            logger.info(f"Upserted {len(bb_plans)} BankBazaar plans with real CSR data")
        else:
            logger.warning("BankBazaar returned no plans — using existing DB data")

        # ── OPTIONAL: PolicyBazaar (may be blocked) ──
        logger.info("Trying PolicyBazaar (optional)...")
        try:
            pb_plans = scrape_policybazaar()
            if pb_plans:
                _upsert_plans(pb_plans, db)
                logger.info(f"Upserted {len(pb_plans)} PolicyBazaar plans")
        except Exception as e:
            logger.info(f"PolicyBazaar skipped: {e}")

        # ── OPTIONAL: InsuranceDekho (may be blocked) ──
        logger.info("Trying InsuranceDekho (optional)...")
        try:
            id_plans = scrape_insurancedekho()
            if id_plans:
                _upsert_plans(id_plans, db)
                logger.info(f"Upserted {len(id_plans)} InsuranceDekho plans")
        except Exception as e:
            logger.info(f"InsuranceDekho skipped: {e}")

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
