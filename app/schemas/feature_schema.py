from pydantic import BaseModel


class FeatureCreate(BaseModel):
    feature_name: str
    enabled: bool
    rollout_percentage: int


class FeatureUpdate(BaseModel):
    enabled: bool