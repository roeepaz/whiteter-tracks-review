import os
from typing import List
import pandas as pd
from recommendation.base import RecommendationStrategy
from config_loader import get_config_value
from flask import jsonify
from custom_types import Event
from events_logic.event_cache import load_event
EVENTS_FOLDER = get_config_value('events_folder')

class TrackIDRecommendation(RecommendationStrategy):
    def recommend(self, event_id, selected_plots) ->List[dict]:
        
        event : Event = load_event(event_id)
        plots_df = event.plots_df.copy()
        correlations_df = event.correlations_df.copy()

        if plots_df.empty or correlations_df.empty:
            raise ValueError(f"Missing or empty data file(s) in event '{event_id}'")

        # Convert selected_plots to a set of tuples (plot_id, system_id)
        selected_set = {(plot['plot_id'], plot['system_id']) for plot in selected_plots}

        # Find track_ids corresponding to the selected plots
        selected_track_ids = correlations_df[
            correlations_df[['plot_id', 'system_id']].apply(tuple, axis=1).isin(selected_set)
        ]['track_id'].unique()

        # Get all plot_ids that belong to these track_ids
        related_plot_keys = correlations_df[
            correlations_df['track_id'].isin(selected_track_ids)
        ][['plot_id', 'system_id']]

        # Merge with plots_df to get full plot details
        merged = plots_df.merge(related_plot_keys, on=['plot_id', 'system_id'])

        return merged.to_dict(orient='records')
