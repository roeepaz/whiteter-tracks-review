import numpy as np
import pandas as pd

from recommendation.base import RecommendationStrategy
from api_utils import minkowski_distance_plus_time
from recommendation.utils import compute_local_eps, compute_local_v_avg
from custom_types import Event
from events_logic.event_cache import load_event
from recommendation.build_tree_cache import (
    build_kdtree_with_cache,
    filter_relevant_plots,
)

class DBSCANRecommendation(RecommendationStrategy):
    def recommend(self, event_id, selected_plots):
        """
        Performs DBSCAN-like clustering on relevant plots.

        Input:
            event_id: str - The ID of the event to analyze
            selected_plots: list[dict] - List of user-selected plots to start clustering from

        Output:
            list[dict] - Plots that were clustered, each with a 'cluster' field

        Explanation:
            Loads the event data, builds a KDTree, filters nearby plots, computes local parameters (v_avg, eps),
            and expands clusters from each selected root using a density-based approach with time + space distance.
        """
        event_data: Event = load_event(event_id)
        if event_data is None or event_id != event_data.event_id:
            raise ValueError("Event not loaded. Please load it first from the UI.")

        df_plots = event_data.plots_df.copy()

        # Step 1: Build or get cached KDTree
        tree, all_keys = build_kdtree_with_cache(df_plots)

        # Step 2: Filter relevant plots near the selected ones
        df = filter_relevant_plots(df_plots, tree, all_keys, selected_plots).reset_index(drop=True)
        df['cluster'] = -1  # default value: not assigned

        # Debug: detect any columns with ndarray issues
        for col in df.columns:
            if isinstance(df[col].iloc[0], np.ndarray):
                print(f"Column {col} contains ndarray!")

        # Step 3: Precompute v_avg and eps per plot
        coords = df[['x', 'y', 'z']].values
        plots = df.to_dict(orient='records')
        df['v_avg'] = compute_local_v_avg(plots, coords)
        df['eps'] = compute_local_eps(plots, df['v_avg'].values)

        # Step 4: Cluster expansion
        cluster_id = 0
        lambda_t = 0.8  # time weighting factor

        for root_plot in selected_plots:
            root_idx = self._find_plot_index(df, root_plot)
            if df.at[root_idx, 'cluster'] != -1:
                continue  # already clustered

            print(f'--> Root {cluster_id}: eps={df.at[root_idx, "eps"]:.2f}, v_avg={df.at[root_idx, "v_avg"]:.2f}')
            df.at[root_idx, 'cluster'] = cluster_id
            self._expand_cluster(df, root_idx, cluster_id, lambda_t)
            cluster_id += 1

        return df[df['cluster'] != -1].to_dict(orient='records')

    def _find_plot_index(self, df, plot):
        """
        Finds the row index of a given plot in the DataFrame.

        Input:
            df: DataFrame - DataFrame containing plot data
            plot: dict - Plot to locate (must contain 'plot_id' and 'system_id')

        Output:
            int - Index of the matching plot

        Explanation:
            Searches for a plot in the DataFrame using both plot_id and system_id.
        """
        matches = df[
            (df['plot_id'] == plot['plot_id']) &
            (df['system_id'] == plot['system_id'])
        ]
        if matches.empty:
            raise ValueError(f"Root plot not found: {plot}")
        return matches.index[0]

    def _expand_cluster(self, df, root_idx, cluster_id, lambda_t):
        """
        Expands a cluster starting from a root plot using breadth-first search (BFS).

        Args:
            df (DataFrame): DataFrame containing plot data with 'v_avg', 'eps', and 'cluster' columns.
            root_idx (int): Index of the root plot to start expansion.
            cluster_id (int): ID to assign to all plots in the cluster.
            lambda_t (float): Time weighting factor for the distance calculation.

        Returns:
            None: The function modifies df in-place by assigning cluster IDs.
        """
        queue = [root_idx]
        visited = set(queue)
        df.at[root_idx, 'cluster'] = cluster_id

        while queue:
            current_idx = queue.pop(0)
            current_plot = df.iloc[current_idx].to_dict()

            avg_v = df.at[current_idx, 'v_avg']
            eps = df.at[current_idx, 'eps']

            # Pre-filter: only consider unvisited, unclustered points
            df_candidates = df[
                (df['cluster'] == -1) & (~df.index.isin(visited))
            ]

            for neighbor_idx, neighbor_row in df_candidates.iterrows():
                neighbor_plot = neighbor_row.to_dict()

                distance = minkowski_distance_plus_time(
                    current_plot, neighbor_plot,
                    lambda_t=lambda_t, v_avg=avg_v
                )

                if distance < eps:
                    df.at[neighbor_idx, 'cluster'] = cluster_id
                    visited.add(neighbor_idx)
                    queue.append(neighbor_idx)
