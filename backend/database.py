from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./insurance.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class InsurancePlan(Base):
    __tablename__ = "insurance_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    source = Column(String, nullable=False)          # policybazaar / insurancedekho / seed
    sum_assured_min = Column(Float, default=0)       # in lakhs
    sum_assured_max = Column(Float, default=0)       # in lakhs
    premium_annual = Column(Float, default=0)        # annual premium in INR (indicative)
    policy_term_min = Column(Integer, default=5)     # years
    policy_term_max = Column(Integer, default=40)    # years
    age_min = Column(Integer, default=18)
    age_max = Column(Integer, default=65)
    claim_settlement_ratio = Column(Float, default=0)  # percentage
    key_features = Column(String, default="")        # pipe-separated features
    source_url = Column(String, default="")
    scraped_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
