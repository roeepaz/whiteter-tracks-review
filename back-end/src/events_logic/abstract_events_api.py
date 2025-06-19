from abc import ABC, abstractmethod
from typing import List, Any
from custom_types import EventWithWhiteTracks

class AbstractEventsAPI(ABC):
    @abstractmethod
    def get_events_ids_list(self) -> List[str]:
        """Return a list of all event IDs.

        Returns:
            List of event folder names.
        """
        raise NotImplementedError("Method:'get_events_ids_list' hasn't been implemented yet.")


    @abstractmethod
    def get_event_data(self, event_id: str) -> EventWithWhiteTracks:
        """Retrieve data for a specific event.

        Parameters:
            event_id: The ID of the event to fetch.

        Returns:
            Event data (plots, tracks, correlations), format defined by implementation.
        """
        raise NotImplementedError("Method:'get_event_data' hasn't been implemented yet.")


    @abstractmethod
    def close_event(self, event_id: str, tracks: Any, notes: str) -> None:
        """Finalize and close an event by saving tracks and notes.

        Parameters:
            event_id: ID of the event to close.
            track: User-defined track data to save.
            notes: General notes for the event closure.
        """
        raise NotImplementedError("Method:'close_event' hasn't been implemented yet.")
