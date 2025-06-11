from typing import List
import pandas as pd
from recommendation.AbstractRecommendationStrategy import AbstractRecommendationStrategy
from events_logic.event_cache import load_event

class TrackIDRecommendation(AbstractRecommendationStrategy):
    def recommend(self, event_id: str, selected_plots: List[dict]) -> List[dict]:
        """Return all plots whose track_id matches any of the user’s selected plots.

        Parameters:
            event_id (str): ID of the event to analyze.
            selected_plots (List[dict]): Seed plots, each with 'plot_id' and 'system_id'.

        Returns:
            List[dict]: Full plot records for all matching track IDs.

        Raises:
            ValueError: If no plot or track data is available for the event.
        """
        plots_df = load_event(event_id).plots_df

        if plots_df.empty or 'track_id' not in plots_df.columns:
            raise ValueError(f"No plot or track data for event '{event_id}'")

        if not selected_plots:
            return []

        # Build a DataFrame of unique selected keys
        selected_keys_df = (
            pd.DataFrame.from_records(selected_plots, columns=['plot_id', 'system_id'])
        )

        # Extract unique track_ids for the selected plots
        track_ids = (
            plots_df
            .merge(selected_keys_df, on=['plot_id', 'system_id'])
            ['track_id']
        )

        if track_ids.empty:
            return []
        
        # Return all plots with those track_ids
        return plots_df[plots_df['track_id'].isin(track_ids)].to_dict(orient='records')