from custom_types import EventWithWhiteTracks
from config.config_loader import get_app_config_value, get_constants_config_value
import pandas as pd
from cachetools import LRUCache
from threading import Lock
from pathlib import Path
from utils.helpers.data_utils import safe_csv_read

EVENTS_FOLDER = get_app_config_value("EVENTS_FOLDER")
EVENTS_CACHE_MAXSIZE = get_constants_config_value("EVENTS_CACHE_MAXSIZE")
_event_cache: LRUCache = LRUCache(maxsize=EVENTS_CACHE_MAXSIZE)  # Cache up to 10 events
_event_cache_lock: Lock = Lock()

def load_event(event_id: str) -> EventWithWhiteTracks:
    """Load event data from disk or cache.

    Parameters:
        event_id: ID of the event to load.

    Returns:
        EventWithWhiteTracks

    Notes:
        - Checks cache first and returns if present.
        - Reads raw CSVs from disk.
        - Merges `track_id` into a `plots_with_tracks_id_df`.
        - Caches and returns the enriched Event object.
    """
    with _event_cache_lock:
        if event_id in _event_cache:
            return _event_cache[event_id]

    event_path = Path(EVENTS_FOLDER) / event_id
    if not event_path.exists():
        raise FileNotFoundError(f"Event '{event_id}' not found")
    
    plots_file = get_app_config_value('PLOTS_FILE_NAME')
    plots_correlations_file = get_app_config_value('PLOTS_CORRELATIONS_FILE_NAME')
    white_tracks_file = get_app_config_value('EVENTS_TRACKS_FILE_NAME')
    white_track_correlations_file   = get_app_config_value('EVENTS_PLOTS_TRACK_CORRELATION_FILE_NAME')

    df_plots            = safe_csv_read(event_path / f"{plots_file}.csv")
    correlations_df         = safe_csv_read(event_path / f"{plots_correlations_file}.csv")
    white_tracks_df         = safe_csv_read(event_path / f"{white_tracks_file}.csv")
    white_track_corrs_df    = safe_csv_read(event_path / f"{white_track_correlations_file}.csv")

    # Always produce a plots_with_tracks_id_df
    if not correlations_df.empty and {"plot_id", "system_id", "track_id"}.issubset(correlations_df.columns):
        plots_with_tracks_id_df = df_plots.merge(
            correlations_df[["plot_id", "system_id", "track_id"]],
            on=["plot_id", "system_id"],
            how="left",
        )
        plots_with_tracks_id_df["track_id"] = plots_with_tracks_id_df["track_id"].fillna(-1)
    else:
        plots_with_tracks_id_df = df_plots.copy()
        plots_with_tracks_id_df["track_id"] = -1

    event = EventWithWhiteTracks(
        event_id=event_id,
        df_plots=plots_with_tracks_id_df,
        white_tracks_df=white_tracks_df,
        white_track_correlations_df=white_track_corrs_df
    )

    with _event_cache_lock:
        _event_cache[event_id] = event

    return event

def clear_event(event_id: str) -> None:
    """Clear a specific event from the cache.

    Parameters:
        event_id: ID of the event to remove from the cache.

    Notes:
        Thread-safe removal of an event from the LRU cache to free memory
        or force a reload on next access.
    """
    with _event_cache_lock:
        _event_cache.pop(event_id, None)
