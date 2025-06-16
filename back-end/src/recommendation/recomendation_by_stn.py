from typing import List
import pandas as pd
import os
from config_loader import get_app_config_value
from recommendation.abstract_recommendation_strategy import AbstractRecommendationStrategy
from custom_types import EventWithWhiteTracks
from events_logic.event_cache import load_event

class STNRecommendation(AbstractRecommendationStrategy):
    def recommend(self, event_id, selected_plots) -> List[dict]:
        
        event : EventWithWhiteTracks = load_event(event_id)
        df_plots = event.df_plots.copy()
        
        
        # Extract all unique (system_id, STN) pairs from the selected plots
        selected_pairs = {(plot['system_id'], plot['STN']) for plot in selected_plots}

        # Filter the DataFrame to include only rows with matching (system_id, STN) pairs
        mask = df_plots.apply(lambda row: (row['system_id'], row['STN']) in selected_pairs, axis=1)

        result = df_plots[mask].to_dict(orient='records')

        return result
