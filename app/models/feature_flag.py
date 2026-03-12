from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    feature_name = Column(String, unique=True, index=True)
    enabled = Column(Boolean, default=False)