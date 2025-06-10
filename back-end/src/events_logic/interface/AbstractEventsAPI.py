from abc import ABC, abstractmethod
from typing import List, Any
from custom_types import Event

class AbstractEventsAPI(ABC):
    @abstractmethod
    def get_events_ids_list(self) -> List[str]:
        """Return a list of all event IDs.

        Returns:
            List[str]: List of event folder names.
        """
        pass

    @abstractmethod
    def get_event_data(self, event_id: str) -> Event:
        """Retrieve data for a specific event.

        Parameters:
            event_id (str): The ID of the event to fetch.

        Returns:
            Any: Event data (plots, tracks, correlations), format defined by implementation.
        """
        pass

    @abstractmethod
    def close_event(self, event_id: str, tracks: Any, notes: str) -> None:
        """Finalize and close an event by saving tracks and notes.

        Parameters:
            event_id (str): ID of the event to close.
            tracks (Any): User-defined track data to save.
            notes (str): General notes for the event closure.

        Returns:
            None
        """
        pass
