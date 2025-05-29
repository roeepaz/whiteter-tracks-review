from abc import ABC, abstractmethod
from typing import List, Any

class EventsInterface(ABC):
    @abstractmethod
    def get_events_ids_list(self) -> List[str]:
        """Return a list of event IDs."""
        pass

    @abstractmethod
    def get_event_data(self, event_id: str) -> Any:
        """Return event data for a given event ID."""
        pass

    @abstractmethod
    def close_event(self, event_id: str, tracks: Any, notes: str) -> None:
        """Close an event with the given tracks and notes."""
        pass
