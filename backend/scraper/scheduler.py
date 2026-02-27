"""
APScheduler-based periodic scraper.
Sources (in priority order):
  1. PolicyX        — live comparison table (requests + BS4)
  2. Coverfox        — live CSR data table   (requests + BS4)
  3. CoverfoxCSR     — dedicated CSR ratio page (requests + BS4)
  4. MaxLife         — Axis Max Life official site plans (requests + BS4)
  5. HDFCLife        — HDFC Life official site plans (requests + BS4)
  6. BankBazaar      — live comparison table (requests + BS4)
  7. Seed data       — guaranteed fallback    (hardcoded, 29 plans)
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, InsurancePlan
from scraper.seed_data import SEED_PLANS
from scraper.bankbazaar import scrape_bankbazaar
from scraper.policyx import scrape_policyx
from scraper.coverfox import scrape_coverfox
from scraper.coverfox_csr import scrape_coverfox_csr
from scraper.maxlife import scrape_maxlife
from scraper.hdfclife import scrape_hdfclife
from scraper.policybazaar import scrape_policybazaar
from scraper.insurancedekho import scrape_insurancedekho

logger = logging.getLogger(__name__)


def _upsert_plans(plans: list, db: Session):
    """Insert or update plans matched by plan_name + provider."""
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
    Full scrape job — runs all sources, seeds if DB is empty.
    Order: seed (if empty) → PolicyX → Coverfox → CoverfoxCSR → MaxLife → HDFCLife → BankBazaar → PolicyBazaar → InsuranceDekho
    """
    db = SessionLocal()
    try:
        total = db.query(InsurancePlan).count()

        # Always ensure seed data is present
        if total == 0:
            logger.info("DB empty — seeding with 29 fallback plans")
            _upsert_plans(SEED_PLANS, db)

        # ── 1. PolicyX (primary — server-side HTML, reliable) ──────────
        logger.info("Scraping PolicyX…")
        try:
            px_plans = scrape_policyx()
            if px_plans:
                _upsert_plans(px_plans, db)
                logger.info(f"PolicyX: upserted {len(px_plans)} plans")
            else:
                logger.info("PolicyX: no plans returned")
        except Exception as e:
            logger.warning(f"PolicyX failed: {e}")

        # ── 2. Coverfox (live CSR + plan details) ──────────────────────
        logger.info("Scraping Coverfox…")
        try:
            cf_plans = scrape_coverfox()
            if cf_plans:
                _upsert_plans(cf_plans, db)
                logger.info(f"Coverfox: upserted {len(cf_plans)} plans")
            else:
                logger.info("Coverfox: no plans returned")
        except Exception as e:
            logger.warning(f"Coverfox failed: {e}")

        # ── 3. CoverfoxCSR (dedicated CSR ratio page) ──────────────────
        logger.info("Scraping Coverfox CSR page…")
        try:
            csr_plans = scrape_coverfox_csr()
            if csr_plans:
                _upsert_plans(csr_plans, db)
                logger.info(f"CoverfoxCSR: upserted {len(csr_plans)} plans")
            else:
                logger.info("CoverfoxCSR: no plans returned")
        except Exception as e:
            logger.warning(f"CoverfoxCSR failed: {e}")

        # ── 4. MaxLife (Axis Max Life official site) ────────────────────
        logger.info("Scraping MaxLife…")
        try:
            ml_plans = scrape_maxlife()
            if ml_plans:
                _upsert_plans(ml_plans, db)
                logger.info(f"MaxLife: upserted {len(ml_plans)} plans")
            else:
                logger.info("MaxLife: no plans returned")
        except Exception as e:
            logger.warning(f"MaxLife failed: {e}")

        # ── 5. HDFCLife (HDFC Life official site) ──────────────────────
        logger.info("Scraping HDFCLife…")
        try:
            hdfc_plans = scrape_hdfclife()
            if hdfc_plans:
                _upsert_plans(hdfc_plans, db)
                logger.info(f"HDFCLife: upserted {len(hdfc_plans)} plans")
            else:
                logger.info("HDFCLife: no plans returned")
        except Exception as e:
            logger.warning(f"HDFCLife failed: {e}")

        # ── 6. BankBazaar (CSR comparison table) ───────────────────────
        logger.info("Scraping BankBazaar…")
        try:
            bb_plans = scrape_bankbazaar()
            if bb_plans:
                _upsert_plans(bb_plans, db)
                logger.info(f"BankBazaar: upserted {len(bb_plans)} plans")
            else:
                logger.info("BankBazaar: no plans returned")
        except Exception as e:
            logger.warning(f"BankBazaar failed: {e}")

        # ── 7. PolicyBazaar (optional, may be blocked) ─────────────────
        logger.info("Trying PolicyBazaar (optional)…")
        try:
            pb_plans = scrape_policybazaar()
            if pb_plans:
                _upsert_plans(pb_plans, db)
                logger.info(f"PolicyBazaar: upserted {len(pb_plans)} plans")
        except Exception as e:
            logger.info(f"PolicyBazaar skipped: {e}")

        # ── 8. InsuranceDekho (optional, may be blocked) ───────────────
        logger.info("Trying InsuranceDekho (optional)…")
        try:
            id_plans = scrape_insurancedekho()
            if id_plans:
                _upsert_plans(id_plans, db)
                logger.info(f"InsuranceDekho: upserted {len(id_plans)} plans")
        except Exception as e:
            logger.info(f"InsuranceDekho skipped: {e}")

        final_count = db.query(InsurancePlan).count()
        logger.info(f"Scrape complete. Total plans in DB: {final_count}")

    except Exception as e:
        logger.error(f"Scrape job error: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start APScheduler that runs scrape every 12 hours."""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scrape_job,
        trigger="interval",
        hours=12,
        id="scrape_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — scrape runs every 12 hours")
    return scheduler

