import numpy as np
import pandas as pd
from typing import List
from recommendation.abstract_recommendation_strategy import AbstractRecommendationStrategy
from utils.distance_metrics import minkowski_distance_plus_time
from recommendation.utils import compute_local_eps, compute_local_v_avg
from custom_types import EventWithWhiteTracks
from events_logic.event_cache import load_event
from config_loader import get_constants_config_value
from recommendation.build_tree_cache import (
    build_kdtree_with_cache,
    filter_relevant_plots,
)
DEFAULT_LAMBDA_T = get_constants_config_value("DEFAULT_TIME_WEIGHT")

class DBSCANRecommendation(AbstractRecommendationStrategy):
    def recommend(self, event_id: str, selected_plots: List[dict]) -> List[dict]:
        """Perform DBSCAN-like clustering on relevant plots.

        Parameters:
            event_id: ID of the event to analyze.
            selected_plots: User-selected plots to start clustering from.

        Returns:
            Clustered plots, each containing a 'cluster' field.

        Notes:
            - Loads event data via `load_event`.
            - Builds or retrieves a KDTree of all plots.
            - Filters nearby plots around each selected root.
            - Computes local parameters (v_avg, eps) per plot.
            - Expands clusters from each root using a density‐based metric combining spatial and temporal distance.
        """
        event_data: EventWithWhiteTracks = load_event(event_id)
        if event_data is None or event_id != event_data.event_id:
            raise ValueError("Event not loaded. Please load it first from the UI.")

        df_plots = event_data.df_plots.copy()

        # Step 1: Build or get cached KDTree
        tree, all_keys = build_kdtree_with_cache(df_plots)

        # Step 2: Filter relevant plots near the selected ones
        df_filtered_plots = filter_relevant_plots(df_plots, tree, all_keys, selected_plots).reset_index(drop=True)
        df_filtered_plots['cluster'] = -1  # default value: not assigned

        # Debug: detect any columns with ndarray issues
        for col in df_filtered_plots.columns:
            if isinstance(df_filtered_plots[col].iloc[0], np.ndarray):
                print(f"Column {col} contains ndarray!")

        # Step 3: Precompute v_avg and eps per plot
        coords = df_filtered_plots[['x', 'y', 'z']].values
        plots = df_filtered_plots.to_dict(orient='records')
        df_filtered_plots['v_avg'] = compute_local_v_avg(plots, coords)
        df_filtered_plots['eps'] = compute_local_eps(plots, df_filtered_plots['v_avg'].values)

        # Step 4: Cluster expansion
        cluster_id = 0

        for root_plot in selected_plots:
            root_idx = self._find_plot_index(df_filtered_plots, root_plot)
            if df_filtered_plots.at[root_idx, 'cluster'] != -1:
                continue  # already clustered

            print(f'--> Root {cluster_id}: eps={df_filtered_plots.at[root_idx, "eps"]:.2f}, v_avg={df_filtered_plots.at[root_idx, "v_avg"]:.2f}')
            df_filtered_plots.at[root_idx, 'cluster'] = cluster_id
            self._expand_cluster(df_filtered_plots, root_idx, cluster_id, DEFAULT_LAMBDA_T)
            cluster_id += 1

        return df_filtered_plots[df_filtered_plots['cluster'] != -1].to_dict(orient='records')

    def _find_plot_index(self, df: pd.DataFrame, plot: dict) -> int:
        """Find the row index of a given plot in the DataFrame.

        Parameters:
            df: DataFrame containing plot data.
            plot: Plot record, must include 'plot_id' and 'system_id' keys.

        Returns:
            int: Index of the matching plot row in `df`.

        Raises:
            ValueError: If no matching plot is found.
        """
        matches = df[
            (df['plot_id'] == plot['plot_id']) &
            (df['system_id'] == plot['system_id'])
        ]
        if matches.empty:
            raise ValueError(f"Root plot not found: {plot}")
        return matches.index[0]

    def _expand_cluster(
        self,
        df_filtered_plots: pd.DataFrame,
        root_idx: int,
        cluster_id: int,
        DEFAULT_LAMBDA_T: float = DEFAULT_LAMBDA_T
    ) -> None:
        """Expand a cluster from a root plot using breadth-first search.

        Parameters:
            df: DataFrame containing plot data with columns
                'v_avg', 'eps', and 'cluster'.
            root_idx: Index of the root plot to start expansion.
            cluster_id: Cluster ID to assign to all reachable plots.
            lambda_t Time weight factor for the distance calculation.

        Returns:
            None: Modifies `df` in place by assigning `cluster_id` to each plot.

        Notes:
            - Uses each plot’s local `eps` and `v_avg` to decide connectivity.
            - Performs a BFS, enqueuing neighbors within the time-weighted Minkowski distance.
        """
        queue = [root_idx]
        visited = set(queue)
        df_filtered_plots.at[root_idx, 'cluster'] = cluster_id

        while queue:
            current_idx = queue.pop(0)
            current_plot = df_filtered_plots.iloc[current_idx].to_dict()

            avg_v = df_filtered_plots.at[current_idx, 'v_avg']
            eps = df_filtered_plots.at[current_idx, 'eps']

            # Pre-filter: only consider unvisited, unclustered points
            df_candidates = df_filtered_plots[
                (df_filtered_plots['cluster'] == -1) & (~df_filtered_plots.index.isin(visited))
            ]

            for neighbor_idx, neighbor_row in df_candidates.iterrows():
                neighbor_plot = neighbor_row.to_dict()

                distance = minkowski_distance_plus_time(
                    current_plot, neighbor_plot,
                    lambda_t=DEFAULT_LAMBDA_T, v_avg=avg_v
                )

                if distance < eps:
                    df_filtered_plots.at[neighbor_idx, 'cluster'] = cluster_id
                    visited.add(neighbor_idx)
                    queue.append(neighbor_idx)
