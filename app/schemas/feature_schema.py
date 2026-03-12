from pydantic import BaseModel


class FeatureCreate(BaseModel):
    feature_name: str
    enabled: bool


class FeatureUpdate(BaseModel):
    enabled: bool