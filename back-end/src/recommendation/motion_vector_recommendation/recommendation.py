from typing import List
import pandas as pd
import numpy as np
from recommendation.AbstractRecommendationStrategy import AbstractRecommendationStrategy
from recommendation.motion_vector_recommendation.clustering import split_initial_clusters, expand_cluster, custom_adaptive_dbscan
from recommendation.motion_vector_recommendation.vector_utils import create_motion_vector, calc_future_center_of_mass, calc_distance_between_two_center_mass, calc_representative_center_of_mass
from recommendation.motion_vector_recommendation.validation import is_valid_cluster
from recommendation.utils import compute_local_eps, compute_local_v_avg
from utils.distance_metrics import minkowski_distance_plus_time
from events_logic.event_cache import load_event
from custom_types import EventWithWhiteTracks
from config_loader import get_constants_config_value

MIN_VALID_CLUSTER_SIZE = get_constants_config_value("MIN_VALID_CLUSTER_SIZE")
MAX_CLUSTER_EXPANSION_ATTEMPTS = get_constants_config_value("MAX_CLUSTER_EXPANSION_ATTEMPTS")
EVENT_CLUSTER_ID_START = get_constants_config_value("EVENT_CLUSTER_ID_START")

SPATIOTEMPORAL_JUMP_LIMIT = get_constants_config_value("SPATIOTEMPORAL_JUMP_LIMIT")
MATCHING_LAMBDA_T = get_constants_config_value("MATCHING_LAMBDA_T")
CENTER_MATCH_LAMBDA_T = get_constants_config_value("CENTER_MATCH_LAMBDA_T")

DEFLECTION_BASE = get_constants_config_value("DEFLECTION_BASE")
DEFLECTION_PER_SECOND = get_constants_config_value("DEFLECTION_PER_SECOND")
DEFLECTION_MAX = get_constants_config_value("DEFLECTION_MAX")


class MotionVectorRecommendation(AbstractRecommendationStrategy): 
    def recommend(self, event_id: str, selected_plots: List[dict]) -> List[dict]:
        """Generate motion vector–based track recommendations.

        Parameters:
            event_id (str): ID of the event to analyze.
            selected_plots (List[dict]): User-selected seed plots.

        Returns:
            List[dict]: Recommended plot records with assigned cluster IDs.

        Notes:
            - Loads all event plots via `load_event`.
            - Computes motion vectors for each selected cluster.
            - Splits and expands clusters based on motion vector continuity.
            - Clusters remaining plots adaptively and matches them to user clusters.
        """
        print("\nStarting motion vector recommendation...")
        event_data : EventWithWhiteTracks = load_event(event_id)

        df_plots = event_data.df_plots.copy()
        df_plots['plot_id'] = df_plots['plot_id'].astype(int)
        df_plots['system_id'] = df_plots['system_id'].astype(int)

        # Step 1: Filter df_plots using KDTree
        # i choose to not filter the plots of the event to an more relative group, 
        # in this recommedation we want to return an complete track
        
        all_plots = df_plots.to_dict(orient='records')
        coords = df_plots[['x', 'y', 'z']].values
        df_plots['plot_key'] = list(zip(df_plots['plot_id'], df_plots['system_id']))

        df_plots['cluster'] = -1
        df_plots['v_avg'] = compute_local_v_avg(all_plots, coords)
        df_plots['eps'] = compute_local_eps(all_plots, df_plots['v_avg'].values)
        df_plots['vector'] = None
        df_plots['center_of_mass'] = None


        df_plots = self._prepare_user_clusters(df_plots, selected_plots)
        df_plots = self._cluster_remaining_plots(df_plots)
        df_plots = self._match_clusters(df_plots)
        df_plots = df_plots.drop(columns=['vector', 'center_of_mass',"plot_key"], errors='ignore')
        final_df = df_plots[df_plots['cluster'] < 1_000].copy()
       # Drop technical columns that are not needed in the final output
        final_df = final_df.drop(columns=['vector', 'center_of_mass',"plot_key"], errors='ignore')
        print(f"\nTotal recommended plots: {len(final_df)}")
        return final_df.to_dict(orient='records')
        
    def _prepare_user_clusters(
        self,
        df_plots: pd.DataFrame,
        selected_plots: List[dict],
    ) -> pd.DataFrame:
        """Build and validate user clusters using motion vectors.

        Parameters:
            df_plots (pd.DataFrame): DataFrame of all event plots.
            selected_plots (List[dict]): User-selected seed plots.
            min_size (int): Minimum number of plots for a valid cluster (default: 7).
            max_attempts (int): Maximum attempts to expand invalid clusters (default: 9).

        Returns:
            pd.DataFrame: The same DataFrame with updated columns:
                - 'cluster': assigned cluster IDs,
                - 'vector': computed motion vectors,
                - 'center_of_mass': cluster centers.

        Notes:
            - Splits user-selected plots into subclusters.
            - Validates each cluster by size and expands with motion vectors if too small.
        """
        print("\nSplitting and validating user clusters...")
        subgroups, _ = split_initial_clusters(selected_plots, df_plots, df_plots[['x','y','z']].values)

        current_cluster_id = 0

        # Small clusters available for expansion
        extra_candidates = [cluster for cluster in subgroups if not is_valid_cluster(cluster, MIN_VALID_CLUSTER_SIZE)]

        for cluster in subgroups:
            attempts = 0
            while not is_valid_cluster(cluster, MIN_VALID_CLUSTER_SIZE) and attempts < MAX_CLUSTER_EXPANSION_ATTEMPTS:
                indices = self._find_cluster_indices(df_plots, cluster)
                v_avg = df_plots.loc[indices, 'v_avg'].mean()
                eps = df_plots.loc[indices, 'eps'].mean()

                cluster = expand_cluster(cluster, df_plots, eps, v_avg, extra_candidates=extra_candidates)

                # Remove absorbed plots from extra_candidates
                extra_candidates = [
                    [p for p in small_cluster if all(not (p['plot_id'] == cp['plot_id'] and p['system_id'] == cp['system_id']) for cp in cluster)]
                    for small_cluster in extra_candidates
                ]
                extra_candidates = [cluster for cluster in extra_candidates if len(cluster) > 0]

                attempts += 1

            if is_valid_cluster(cluster, MIN_VALID_CLUSTER_SIZE):
                cluster_keys = {(p['plot_id'], p['system_id']) for p in cluster}
                indices = df_plots[df_plots['plot_key'].isin(cluster_keys)].index.tolist()

                df_plots.loc[indices, 'cluster'] = current_cluster_id

                vec, center = create_motion_vector(cluster)
                for idx in indices:
                    df_plots.at[idx, 'vector'] = vec
                    df_plots.at[idx, 'center_of_mass'] = center

                current_cluster_id += 1 
            else:
                print(f"Cluster rejected (final size: {len(cluster)})")

        # Final: Mark all leftover plots as -1
        for leftover_cluster in extra_candidates:
            for plot in leftover_cluster:
                condition = (df_plots['plot_id'] == plot['plot_id']) & (df_plots['system_id'] == plot['system_id'])
                df_plots.loc[condition, 'cluster'] = -1

        return df_plots

    def _cluster_remaining_plots(self, df_plots: pd.DataFrame) -> pd.DataFrame:
        """Cluster the remaining unassigned plots using adaptive DBSCAN.

        Parameters:
            df_plots (pd.DataFrame): DataFrame of all event plots; some rows may already have a 'cluster' value.

        Returns:
            pd.DataFrame: The same DataFrame with updated 'cluster' values for previously unassigned plots.

        Notes:
            - Runs a DBSCAN‐style algorithm with locally adaptive `eps` and `v_avg` on the unclustered points.
            - Assigns new cluster IDs starting from 1000 for these additional clusters.
        """
        print("\nClustering remaining event plots...")
        df_remaining = df_plots[df_plots['cluster'] == -1]
        plots = df_remaining.to_dict(orient='records')
        v_avg_list = df_remaining['v_avg'].values
        eps_list = df_remaining['eps'].values

        cluster_array = custom_adaptive_dbscan(df_remaining,plots, v_avg_list, eps_list)
        event_cluster_start_id = EVENT_CLUSTER_ID_START
        cluster_id_map = {}

        for idx, cid in enumerate(cluster_array):
            if cid == -1:
                continue
            real_id = cluster_id_map.setdefault(cid, event_cluster_start_id + len(cluster_id_map))
            row_idx = df_remaining.index[idx]
            df_plots.at[row_idx, 'cluster'] = real_id

        print(f"Total remaining plots: {len(df_remaining)}")
        print(f"Total clusters found: {len(set(cluster_array)) - (1 if -1 in cluster_array else 0)}")
        print(f"Noise points: {np.sum(cluster_array == -1)}")

        return df_plots

    def _match_clusters(self, df_plots: pd.DataFrame) -> pd.DataFrame:
        """Match system-generated event clusters to user clusters based on motion similarity.

        Parameters:
            df_plots (pd.DataFrame): DataFrame containing plots with both user-assigned and system-generated cluster IDs.

        Returns:
            pd.DataFrame: Updated DataFrame where event cluster IDs have been reassigned to match user cluster IDs when similarity criteria are met.

        Notes:
            - For each user cluster, compute its predicted future position.
            - Compare these predictions to each event cluster’s motion path.
            - If the distance falls within a dynamic threshold, reassign the event cluster’s ID to the corresponding user cluster ID.
        """
        print("\nMatching user clusters with event clusters...")

        user_ids = sorted(df_plots[df_plots['cluster'] < EVENT_CLUSTER_ID_START]['cluster'].unique())
        event_ids = sorted(df_plots[df_plots['cluster'] >= EVENT_CLUSTER_ID_START]['cluster'].unique())
        matched = set()
        i = 0

        spatial_temporal_jump_limit = SPATIOTEMPORAL_JUMP_LIMIT  # Max allowed combined (space + time) distance in meters

        while i < len(user_ids):
            uid = user_ids[i]
            u_data = df_plots[df_plots['cluster'] == uid]

            if u_data.empty:
                print(f"Skipping user cluster {uid}: no plots")
                i += 1
                continue

            u_vec = u_data.iloc[0]['vector']
            u_center = u_data.iloc[0]['center_of_mass']

            if u_vec is None or u_center is None:
                print(f"Skipping user cluster {uid}: missing vector or center_of_mass")
                i += 1
                continue

            v_avg_user = u_data['v_avg'].mean()
            best_cid, best_score = None, float('inf')

            # Create fake plots for distance calculation
            user_plot = {
                'x': u_center.x,
                'y': u_center.y,
                'z': u_center.z,
                't': u_center.t
            }

            for eid in event_ids:
                if eid in matched:
                    continue

                e_data = df_plots[df_plots['cluster'] == eid]
                if len(e_data) < 2:
                    continue

                e_center = calc_representative_center_of_mass(e_data.to_dict(orient='records'))
                dt = e_center.t - u_center.t
                if dt <= 0:
                    continue

                event_plot = {
                    'x': e_center.x,
                    'y': e_center.y,
                    'z': e_center.z,
                    't': e_center.t
                }

                v_avg_event = e_data['v_avg'].mean()
                v_avg_avg = (v_avg_user + v_avg_event) / 2

                # New: Use minkowski_distance_plus_time for spatial-temporal jump check
                real_spatial_temporal_dist = minkowski_distance_plus_time(
                    user_plot, event_plot, lambda_t=MATCHING_LAMBDA_T, v_avg=v_avg_avg
                )
                if real_spatial_temporal_dist > spatial_temporal_jump_limit:
                    continue  # too far in space-time, skip

                # Predict multiple future points
                #predicted_centers = self._predict_multiple_centers(u_vec, u_center, dt, num_steps=3)

                # Compute average distance to event cluster center
                predicted = calc_future_center_of_mass(u_vec, u_center, dt)
                avg_dist = calc_distance_between_two_center_mass(predicted, e_center,v_avg_avg,lambda_t=CENTER_MATCH_LAMBDA_T)
                # Dynamic matching limit
                dynamic_limit = self._dynamic_deflection_limit(dt)

                if avg_dist < dynamic_limit and avg_dist < best_score:
                    print(f"---> found good comparing user cluster {i} to event {eid}: avg_dist={avg_dist:.1f} / limit={dynamic_limit:.1f}")
                    best_cid, best_score = eid, avg_dist

            if best_cid is not None:
                print(f"Matched event cluster {best_cid} to user cluster {uid}")
                df_plots.loc[df_plots['cluster'] == best_cid, 'cluster'] = uid

                # Recompute updated user vector and center of mass after merging
                updated_cluster = df_plots[df_plots['cluster'] == uid].to_dict(orient='records')
                new_vec, new_center = create_motion_vector(updated_cluster)
                for idx in df_plots[df_plots['cluster'] == uid].index:
                    df_plots.at[idx, 'vector'] = new_vec
                    df_plots.at[idx, 'center_of_mass'] = new_center

                matched.add(best_cid)
                continue
            else:
                print(f"No match found for user cluster {uid}")

            i += 1

        return df_plots
    
    def _find_cluster_indices(
        self,
        df_plots: pd.DataFrame,
        cluster: List[dict]
    ) -> List[int]:
        """Find DataFrame indices corresponding to a cluster of plots.

        Parameters:
            df_plots (pd.DataFrame): DataFrame of event plots, must include 'plot_key'.
            cluster (List[dict]): Plot dicts with keys 'plot_id' and 'system_id'.

        Returns:
            List[int]: List of indices in `df_plots` that match the given cluster.
        """
        cluster_keys = {(p['plot_id'], p['system_id']) for p in cluster}
        return df_plots[df_plots['plot_key'].isin(cluster_keys)].index.tolist()

    def _dynamic_deflection_limit(
        self,
        dt: float
    ) -> float:
        """Compute dynamic deflection limit based on time delta.

        Parameters:
            dt (float): Time difference between user and event clusters.

        Returns:
            float: Maximum allowed deflection distance, capped by a predetermined maximum.
        """
        return min(DEFLECTION_BASE + DEFLECTION_PER_SECOND * dt, DEFLECTION_MAX)

