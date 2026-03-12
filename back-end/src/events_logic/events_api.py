from datetime import datetime
from typing import List
from pathlib import Path
import pandas as pd
import json
from flask import jsonify
from config.config_loader import get_app_config_value
from events_logic.abstract_events_api import AbstractEventsAPI
from custom_types import EventWithWhiteTracks
from events_logic.event_cache import load_event, clear_event
from enums.event_data_keys import EventDataKey


class EventApi(AbstractEventsAPI):

    def get_events_ids_list(self) -> List[str]:
        """Returns a list of event IDs (folder names) inside EVENTS_FOLDER.

        Returns:
            List of folder names representing event IDs.

        Raises:
            FileNotFoundError: Raised if path not found.
        """
        events_folder = Path(get_app_config_value('EVENTS_FOLDER'))

        if not events_folder.exists():
            raise FileNotFoundError("path to the events not found")
        return [folder.name for folder in events_folder.iterdir() if folder.is_dir()]

    def get_event_data(self, event_id) -> dict:
        """Loads event data for the given event_id.

        Parameters:
            event_id (str): ID of the event to load.

        Returns:
            dict: A mapping with keys:
                1: List of plot records.
                2: List of white track records.
                3: List of white track correlation records.

        Raises:
            FileNotFoundError: Raised if event not found.
        """
        event = load_event(event_id)
        return {
            EventDataKey.PLOTS: event.df_plots.to_dict(orient='records'),
            EventDataKey.WHITE_TRACKS: event.white_tracks_df.to_dict(orient='records'),
            EventDataKey.CORRELATIONS: event.white_track_correlations_df.to_dict(orient='records'),
        }

    def close_event(self, event_id: str, tracks: dict, notes: str) -> None:
        """
        Handles closing an event by saving event plots, tracks, track correlations, and notes.

        Folder Structure:
        events/
            <event_id>/
                plots.csv
                white_tracks.csv (new)
                white_tracks_correlations.csv (new)
                notes.json (new)
        Parameters:
            event_id (str): ID of the event to close.
            tracks (dict): All user-defined tracks and their data.
            notes (str): General notes about the event.

        Returns:
            None

        Notes:
            This method saves:
            - Tracks to 'white_tracks.csv'
            - Plot-track correlations to 'white_tracks_correlations.csv'
            - Event-wide notes to 'notes.json'.
            Tracks are assigned new IDs and saved along with spline points and notes.
        """
        events_folder = Path(get_app_config_value("EVENTS_FOLDER"))
        events_tracks_file_name = get_app_config_value('EVENTS_TRACKS_FILE_NAME')
        events_plots_track_correlation_file_name = get_app_config_value('EVENTS_PLOTS_TRACK_CORRELATION_FILE_NAME')

        events_dir = events_folder / event_id
        tracks_file = events_dir / f"{events_tracks_file_name}.csv"
        correlations_file = events_dir / f"{events_plots_track_correlation_file_name}.csv"
        notes_file = events_dir / "notes.json"

        event: EventWithWhiteTracks = load_event(event_id)
        full_df_plots = event.df_plots.copy()
        all_tracks = []
        next_track_id = get_new_track_id(event)

        for track_data in tracks.values():
            selected_df_plots = pd.DataFrame(track_data.get("selectedPlots", []))
            spline_points_df = pd.DataFrame(track_data.get("splinePoints", []))

            if selected_df_plots.empty:
                continue

            track_id = next_track_id
            next_track_id += 1

            spline_points_df["id"] = track_id
            all_tracks.append(spline_points_df)

            selected_plot_ids = selected_df_plots["plot_id"].astype(str).tolist()
            update_white_tracks_correlations_table(track_id, selected_plot_ids, full_df_plots, correlations_file)

            track_note = track_data.get("trackNote")
            if track_note:
                append_to_json_file("white tracks notes", str(track_id), track_note, notes_file)

        if all_tracks:
            df_all_tracks = pd.concat(all_tracks, ignore_index=True)
            append_to_csv(tracks_file, df_all_tracks)

        append_to_json_file("Sensors that cause problems", datetime.today().strftime("%Y-%m-%d %H:%M"), notes, notes_file)

        clear_event(event_id)


def get_new_track_id(event: EventWithWhiteTracks) -> int:
    """Determines the next available track ID.

    Parameters:
        event: The event object.

    Returns:
        int: The next available track ID, defaults to 1 if none exist.
    """
    df = event.white_tracks_df.copy()
    if not df.empty and "id" in df.columns:
        return int(df["id"].max()) + 1
    return 1


def update_white_tracks_correlations_table(track_id: int, selected_plot_ids: list, full_df_plots: pd.DataFrame, connection_file: Path
) -> None:
    """Updates the correlations table between plots and a track.

    Parameters:
        track_id: The track ID being saved.
        selected_plot_ids: List of plot IDs in the track.
        full_df_plots: All plot data from the event.
        connection_file: Path to the correlations CSV file.
    """
    system_id_map = full_df_plots.copy()
    system_id_map["plot_id"] = system_id_map["plot_id"].astype(str)
    system_id_map = system_id_map.set_index("plot_id")["system_id"].to_dict()

    selected_plot_ids = [str(pid) for pid in selected_plot_ids]

    new_connections = pd.DataFrame({
        "white_track_id": [track_id] * len(selected_plot_ids),
        "plot_id": selected_plot_ids,
        "system_id": [system_id_map.get(pid, -1) for pid in selected_plot_ids]
    })

    if not new_connections.empty:
        append_to_csv(connection_file, new_connections)


def append_to_csv(file_path: Path, df: pd.DataFrame) -> None:
    """Appends a DataFrame to a CSV file.

    Parameters:
        file_path: Path to the CSV file.
        df: Data to append.
    """
    if df.empty:
        return
    write_header = not file_path.exists() or file_path.stat().st_size == 0
    df.to_csv(file_path, mode="a", header=write_header, index=False)


def append_to_json_file(category: str, key: str, data, file_path: Path) -> None:
    """Appends a key-value pair under a category in a JSON file.

    Parameters:
        category: JSON key grouping (e.g., 'white tracks notes').
        key: Sub-key inside the category.
        data: Value to store.
        file_path: Path to the JSON file.

    Explanation:
        Reads existing JSON (or creates new), inserts or updates the value, and writes it back to file.
    """
    if not data or data == "-1":
        return

    try:
        if file_path.exists():
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
    except (json.JSONDecodeError, FileNotFoundError):
        existing_data = {}

    if category not in existing_data:
        existing_data[category] = {}

    if isinstance(data, set):
        data = next(iter(data), None)

    existing_data[category][key] = data

    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=4)