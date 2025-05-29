from abc import ABC, abstractmethod

class RecommendationStrategy(ABC):
    @abstractmethod
    def recommend(self, event_id, selected_plots) -> list[dict]:
        pass
