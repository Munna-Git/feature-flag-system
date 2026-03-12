from fastapi import FastAPI
from app.database import engine, Base
from app.models.feature_flag import FeatureFlag
from app.routers.feature_router import router as feature_router


app = FastAPI()


Base.metadata.create_all(bind = engine)
app.include_router(feature_router)