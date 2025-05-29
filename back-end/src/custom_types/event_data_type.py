from dataclasses import dataclass, field
import pandas as pd
import datetime
#TODO ADD FATHER CLASS AN EN EVENT THAT HAVE WHITE TRACK 
@dataclass
class Event:
    event_id: str
    plots_df: pd.DataFrame
    plots_correlations_df: pd.DataFrame
    white_tracks_df: pd.DataFrame
    white_track_correlations_df: pd.DataFrame
    