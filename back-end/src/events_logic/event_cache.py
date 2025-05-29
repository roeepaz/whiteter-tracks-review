from typing import Dict
from custom_types import Event
from config_loader import get_config_value
import os
import pandas as pd
from cachetools import LRUCache
from threading import Lock

EVENTS_FOLDER = get_config_value("events_folder")
_event_cache: LRUCache = LRUCache(maxsize=10)  # Cache up to 10 events
_event_cache_lock: Lock = Lock()

def load_event(event_id: str) -> Event:
    """
    Loads event data from disk or cache.

    Input:
        event_id: str – The ID of the event to load

    Output:
        Event – An Event object with plots and track data loaded

    Explanation:
        Checks if the event is already cached. If not, loads all relevant CSV files from disk,
        including plots, correlations, and white tracks. Merges correlations into the plots DataFrame.
        Then caches and returns the loaded Event object.
    """
    with _event_cache_lock:
        if event_id in _event_cache:
            return _event_cache[event_id]

    event_path = os.path.join(EVENTS_FOLDER, event_id)
    if not os.path.exists(event_path):
        raise FileNotFoundError(f"Event '{event_id}' not found")

    def safe_read(path):
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

    plots_df = safe_read(os.path.join(event_path, "plots.csv"))
    correlations_df = safe_read(os.path.join(event_path, "plots_correlations.csv"))
    white_tracks_df = safe_read(os.path.join(event_path, f"{get_config_value('events_tracks_file_name')}.csv"))
    white_track_correlations_df = safe_read(os.path.join(event_path, f"{get_config_value('events_plots_track_correlation_file_name')}.csv"))

    # If correlation file is valid, merge track_id into plots
    if not correlations_df.empty and {"plot_id", "system_id", "track_id"}.issubset(correlations_df.columns):
        plots_df = plots_df.merge(
            correlations_df[["plot_id", "system_id", "track_id"]],
            on=["plot_id", "system_id"],
            how="left"
        )
        plots_df["track_id"] = plots_df["track_id"].fillna(-1)

    event = Event(
        event_id=event_id,
        plots_df=plots_df,
        plots_correlations_df=correlations_df,
        white_tracks_df=white_tracks_df,
        white_track_correlations_df=white_track_correlations_df
    )

    with _event_cache_lock:
        _event_cache[event_id] = event

    return event

def clear_event(event_id: str):
    """
    Clears a specific event from the cache.

    Input:
        event_id: str – The ID of the event to remove from the cache

    Output:
        None

    Explanation:
        Thread-safe removal of an event from the LRU cache to free memory or force reload next time.
    """
    with _event_cache_lock:
        _event_cache.pop(event_id, None)
