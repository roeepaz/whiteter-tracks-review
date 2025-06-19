from recommendation.implementations.recomendation_by_stn import STNRecommendation
from recommendation.implementations.recomendation_by_track_id import TrackIDRecommendation
from recommendation.implementations.dbscan import DBSCANRecommendation
from recommendation.implementations.motion_vector_recommendation.recommendation import MotionVectorRecommendation
from recommendation.abstract_recommendation_strategy import AbstractRecommendationStrategy

RECOMMENDATION_MAP: dict[str, type[AbstractRecommendationStrategy]] = {
    "stn": STNRecommendation,
    "trackid": TrackIDRecommendation,
    "dbscan": DBSCANRecommendation,
    "motion_vector": MotionVectorRecommendation,
}

def get_recommendation_base_on_strategy(name: str, event_id: str, selected_plots: list[dict]) -> list[dict]:
    name = name.lower()
    strategy_class = RECOMMENDATION_MAP.get(name)
    
    if strategy_class is None:
        raise ValueError(f"Unknown recommendation type: {name}")

    strategy = strategy_class()
    return strategy.recommend(event_id, selected_plots)
