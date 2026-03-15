from sqlalchemy.orm import Session
from app.models.feature_flag import FeatureFlag
from app.core.cache import redis_client
import json
import hashlib

def get_features(db):

    cache_key = "all_features"

    cached_data = redis_client.get(cache_key)

    if cached_data:
        print("CACHE HIT")
        return json.loads(cached_data)

    print("CACHE MISS")

    features = db.query(FeatureFlag).all()

    result = {}

    for feature in features:
        result[feature.feature_name] = feature.enabled

    response = {"features": result}

    redis_client.set(cache_key, json.dumps(response))

    return response


def create_feature(db, feature_name, enabled, rollout_percentage):

    new_feature = FeatureFlag(
        feature_name=feature_name,
        enabled=enabled,
        rollout_percentage=rollout_percentage
    )

    db.add(new_feature)
    db.commit()

    redis_client.delete("all_features")

    return {"message": "Feature created successfully"}

    
def update_feature(db, feature_name, enabled, rollout_percentage):

    feature = db.query(FeatureFlag).filter(
        FeatureFlag.feature_name == feature_name
    ).first()

    if not feature:
        return {"error": "Feature not found"}

    feature.enabled = enabled
    feature.rollout_percentage = rollout_percentage

    db.commit()

    redis_client.delete("all_features")

    return {"message": "Feature updated successfully"}


def delete_feature(db, feature_name):
    feature = db.query(FeatureFlag).filter(
        FeatureFlag.feature_name == feature_name,
    ).first()

    if not feature:
        return {"error": "Feature not found"}

    db.delete(feature)
    db.commit()

    redis_client.delete("all_features")

    return {"message": "Feature deleted successfully"}
    

def is_feature_enabled(feature, user_id):

    if not feature.enabled:
        return False

    if feature.rollout_percentage == 100:
        return True

    user_hash = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)

    bucket = user_hash % 100

    return bucket < feature.rollout_percentage


def get_feature_for_user(db, feature_name, user_id):

    feature = db.query(FeatureFlag).filter(
        FeatureFlag.feature_name == feature_name
    ).first()

    if not feature:
        return {"error": "Feature not found"}

    enabled = is_feature_enabled(feature, user_id)

    return {
        "feature": feature_name,
        "enabled": enabled
    }