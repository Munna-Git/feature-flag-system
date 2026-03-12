from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.feature_service import get_features
from app.schemas.feature_schema import FeatureCreate, FeatureUpdate
from app.services.feature_service import create_feature, update_feature, delete_feature


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/features")
def read_features(db: Session = Depends(get_db)):

    result = get_features(db)

    return result

@router.post("/features")
def create_new_feature(feature: FeatureCreate, db: Session = Depends(get_db)):

    result = create_feature(
        db,
        feature.feature_name,
        feature.enabled
    )

    return result

@router.put("/features/{feature_name}")
def update_existing_feature(
    feature_name: str,
    feature: FeatureUpdate,
    db: Session = Depends(get_db)
):

    result = update_feature(
        db,
        feature_name,
        feature.enabled
    )

    return result


@router.delete("/features/{feature_name}")
def delete_existing_feature(
    feature_name: str,
    db: Session = Depends(get_db)
):

    result = delete_feature(db, feature_name)

    return result