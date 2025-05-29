from datetime import datetime
import pandas as pd
import json
import os
from flask import jsonify
from config_loader import get_config_value
from events_logic.interface.events_interface import EventsInterface
from custom_types import Event
from events_logic.event_cache import load_event, clear_event

EVENTS_FOLDER = get_config_value('events_folder')

class EventApi(EventsInterface):

    def get_events_ids_list(self):
        """
        Returns a list of event IDs (folder names) inside EVENTS_FOLDER.

        Input:
            None

        Output:
            list[str] – List of folder names representing event IDs.
            On error: JSON error with HTTP 404.

        Explanation:
            Checks if the events folder exists. If yes, returns all folder names (event IDs) inside it.
        """
        if not os.path.exists(EVENTS_FOLDER):
            return jsonify({"error": f"path to the events not found"}), 404
        return [folder for folder in os.listdir(EVENTS_FOLDER) if os.path.isdir(os.path.join(EVENTS_FOLDER, folder))]

    def get_event_data(self, event_id):
        """
        Loads event data for the given event_id.

        Input:
            event_id: str – ID of the event to load

        Output:
            dict:
                1: List of plot records
                2: List of white track records
                3: List of white track correlation records
            On error: JSON error with HTTP 404

        Explanation:
            Loads the event and returns all its key data in record format (plot data, tracks, correlations).
        """
        try:
            event = load_event(event_id)
            return {
                1: event.plots_df.to_dict(orient='records'),
                2: event.white_tracks_df.to_dict(orient='records'),
                3: event.white_track_correlations_df.to_dict(orient='records'),
            }
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 404

    def close_event(self, event_id: str, tracks: dict, notes: str):
        """
        Handles closing an event by saving event plots, tracks, track correlations, and notes.
        - Saves tracks to `white_tracks.csv`
        - Saves track-plot correlations to `white_tracks_correlations.csv`
        - Stores event-wide notes in `notes.json`, including per-track notes

        Folder Structure:
        events/
            <event_id>/
                plots.csv
                white_tracks.csv
                white_tracks_correlations.csv
                notes.json
        Input:
            event_id: str – ID of the event to close
            tracks: dict – All user-defined tracks and their data
            notes: str – General notes about the event

        Output:
            None

        Explanation:
            Saves tracks to 'white_tracks.csv', correlations to 'white_tracks_correlations.csv', and notes to 'notes.json'.
            Tracks are assigned new IDs. Each track's selected plots and notes are also saved.
        """
        EVENTS_DIR = os.path.join(get_config_value("events_folder"), event_id)
        TRACKS_FILE = os.path.join(EVENTS_DIR, f"{get_config_value('events_tracks_file_name')}.csv")
        CORRELATIONS_FILE = os.path.join(EVENTS_DIR, f"{get_config_value('events_plots_track_correlation_file_name')}.csv")
        NOTES_FILE = os.path.join(EVENTS_DIR, "notes.json")

        event: Event = load_event(event_id)
        full_plots_df = event.plots_df.copy()
        all_tracks = []
        next_track_id = get_new_track_id(event)

        for track_data in tracks.values():
            selected_plots_df = pd.DataFrame(track_data.get("selectedPlots", []))
            spline_points_df = pd.DataFrame(track_data.get("splinePoints", []))

            if selected_plots_df.empty:
                continue

            track_id = next_track_id
            next_track_id += 1

            spline_points_df["id"] = track_id
            all_tracks.append(spline_points_df)

            selected_plot_ids = selected_plots_df["plot_id"].astype(str).tolist()
            update_white_tracks_correlations_table(track_id, selected_plot_ids, full_plots_df, CORRELATIONS_FILE)

            track_note = track_data.get("trackNote")
            if track_note:
                append_to_json_file("white tracks notes", str(track_id), track_note, NOTES_FILE)

        if all_tracks:
            df_all_tracks = pd.concat(all_tracks, ignore_index=True)
            append_to_csv(TRACKS_FILE, df_all_tracks)

        append_to_json_file("Sensors that cause problems", datetime.today().strftime("%Y-%m-%d %H:%M"), notes, NOTES_FILE)

        clear_event(event_id)


def get_new_track_id(event: Event) -> int:
    """
    Determines the next available track ID.

    Input:
        event: Event – The event object

    Output:
        int – The next available track ID

    Explanation:
        Finds the max existing track ID and returns the next value. Defaults to 1 if none exist.
    """
    df = event.white_tracks_df.copy()
    if not df.empty and "id" in df.columns:
        return int(df["id"].max()) + 1
    return 1


def update_white_tracks_correlations_table(track_id: int, selected_plot_ids: list, full_plots_df: pd.DataFrame, connection_file: str):
    """
    Updates the correlations table between plots and a track.

    Input:
        track_id: int – The track ID being saved
        selected_plot_ids: list – List of plot IDs in the track
        full_plots_df: DataFrame – All plot data from the event
        connection_file: str – Path to the correlations CSV file

    Output:
        None

    Explanation:
        Creates a new DataFrame mapping plot IDs to the track and appends it to the CSV.
    """
    system_id_map = full_plots_df.copy()
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


def append_to_csv(file_path: str, df: pd.DataFrame):
    """
    Appends a DataFrame to a CSV file.

    Input:
        file_path: str – Path to the CSV file
        df: DataFrame – Data to append

    Output:
        None

    Explanation:
        Appends the data to the file, adding a header if the file is new or empty.
    """
    if df.empty:
        return
    write_header = not os.path.exists(file_path) or os.stat(file_path).st_size == 0
    df.to_csv(file_path, mode="a", header=write_header, index=False)


def append_to_json_file(category: str, key: str, data, file_path: str):
    """
    Appends a key-value pair under a category in a JSON file.

    Input:
        category: str – JSON key grouping (e.g., 'white tracks notes')
        key: str – Sub-key inside the category
        data: any – Value to store
        file_path: str – Path to the JSON file

    Output:
        None

    Explanation:
        Reads existing JSON (or creates new), inserts or updates the value, and writes it back to file.
    """
    if not data or data == "-1":
        return

    try:
        if os.path.exists(file_path):
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
