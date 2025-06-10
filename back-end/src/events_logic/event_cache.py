from custom_types import EventWithWhiteTracks
from config_loader import get_config_value
import pandas as pd
from cachetools import LRUCache
from threading import Lock
from pathlib import Path

EVENTS_FOLDER = get_config_value("events_folder")
_event_cache: LRUCache = LRUCache(maxsize=10)  # Cache up to 10 events
_event_cache_lock: Lock = Lock()


def load_event(event_id: str) -> EventWithWhiteTracks:
    """Load event data from disk or cache.

    Parameters:
        event_id (str): ID of the event to load.

    Returns:
        Event: An Event object containing plots, white tracks, and plot–track correlations.

    Notes:
        - Checks if the event is already cached; if so, returns it immediately.
        - Otherwise, reads `plots.csv`, `white_tracks.csv`, and `white_tracks_correlations.csv` from disk.
        - Merges the correlation data into the plots DataFrame.
        - Caches the loaded Event object before returning.
    """
    with _event_cache_lock:
        if event_id in _event_cache:
            return _event_cache[event_id]

    event_path = Path(EVENTS_FOLDER) / event_id
    if not event_path.exists():
        raise FileNotFoundError(f"Event '{event_id}' not found")

    def safe_read(path: Path) -> pd.DataFrame:
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
    
    events_tracks_file_name = get_config_value('events_tracks_file_name')
    events_plots_track_correlation_file_name = get_config_value('events_plots_track_correlation_file_name')

    plots_df = safe_read(event_path / "plots.csv")
    correlations_df = safe_read(event_path / "plots_correlations.csv")
    white_tracks_df = safe_read(event_path / f"{events_tracks_file_name}.csv")
    white_track_correlations_df = safe_read(event_path / f"{events_plots_track_correlation_file_name}.csv")

    # If correlation file is valid, merge track_id into plots
    if not correlations_df.empty and {"plot_id", "system_id", "track_id"}.issubset(correlations_df.columns):
        plots_df = plots_df.merge(
            correlations_df[["plot_id", "system_id", "track_id"]],
            on=["plot_id", "system_id"],
            how="left"
        )
        plots_df["track_id"] = plots_df["track_id"].fillna(-1)

    event = EventWithWhiteTracks(
        event_id=event_id,
        plots_df=plots_df,
        plots_correlations_df=correlations_df,
        white_tracks_df=white_tracks_df,
        white_track_correlations_df=white_track_correlations_df
    )

    with _event_cache_lock:
        _event_cache[event_id] = event

    return event

def clear_event(event_id: str) -> None:
    """Clear a specific event from the cache.

    Parameters:
        event_id (str): ID of the event to remove from the cache.

    Notes:
        Thread-safe removal of an event from the LRU cache to free memory
        or force a reload on next access.
    """
    with _event_cache_lock:
        _event_cache.pop(event_id, None)
