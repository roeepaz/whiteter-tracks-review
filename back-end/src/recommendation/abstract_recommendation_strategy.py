from abc import ABC, abstractmethod
from typing import List

class AbstractRecommendationStrategy(ABC):
    """An abstract base class for recommendation strategies.
    
    Each subclass must implement the `recommend` method,
    which returns a list of recommended plots based on the
    given event ID and selected plots.
    """

    @abstractmethod
    def recommend(self, event_id: str, selected_plots: List[dict]) -> List[dict]:
        """Generate a list of recommended plots.

        Parameters:
            event_id: The ID of the event to base recommendations on.
            selected_plots: A list of selected plot data.

        Returns:
            A list of recommended plots.
        """
        raise NotImplementedError("Method:'recommend' hasn't been implemented yet.")
