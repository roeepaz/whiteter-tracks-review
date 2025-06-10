from typing import List
import pandas as pd
import os
from config_loader import get_config_value
from recommendation.base import RecommendationStrategy
from custom_types import Event
from events_logic.event_cache import load_event
class STNRecommendation(RecommendationStrategy):
    def recommend(self, event_id, selected_plots) -> List[dict]:
        
        event : Event = load_event(event_id)
        plots_df = event.plots_df.copy()
        
        
        # Extract all unique (system_id, STN) pairs from the selected plots
        selected_pairs = {(plot['system_id'], plot['STN']) for plot in selected_plots}

        # Filter the DataFrame to include only rows with matching (system_id, STN) pairs
        mask = plots_df.apply(lambda row: (row['system_id'], row['STN']) in selected_pairs, axis=1)

        result = plots_df[mask].to_dict(orient='records')

        return result
