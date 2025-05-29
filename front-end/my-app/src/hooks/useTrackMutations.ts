import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { submitPlots, sentEventTracks, getRecommendation } from "../API/apiServer";
import { TrackPlot, Plot, TrackData } from "../type/types";
import { clearPersistentState } from '../hooks/usePersistentState';


interface UseTrackMutationsParams {
  setViewTrack: React.Dispatch<React.SetStateAction<TrackPlot[]>>;
  setUiTracks: React.Dispatch<React.SetStateAction<Record<number, TrackData>>>;
  setSelectedPlots: React.Dispatch<React.SetStateAction<Plot[]>>;
  UiTracks: Record<number, TrackData>;
  eventNotes: number[];
  eventId : string | undefined;
  recommendationType: string
}

export const useTrackMutations = ({
  setViewTrack,
  setUiTracks,
  setSelectedPlots,
  UiTracks,
  eventNotes,
  eventId,
  recommendationType
}: UseTrackMutationsParams) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Mutation for creating a track
  const createTrackMutation = useMutation<TrackPlot[], Error,{ selectedPlots: Plot[]; smoothingFactor: number }>({
    mutationFn: submitPlots,
    onSuccess: (data: TrackPlot[]) => {
      setViewTrack(data);
      console.log("Track created successfully");
    },
    onError: (error: Error) => {
      console.error("Error creating track:", error);
      alert(`Failed to create track: ${error.message}`);
    },
  });

  // Mutation for closing the event
  const closeEventMutation = useMutation<void, Error, void>({
    mutationFn: async () => {
        await sentEventTracks(eventId, UiTracks, eventNotes); // Ignore the response explicitly
      },    onSuccess: () => {
      console.log("Tracks and notes successfully submitted");
      setUiTracks({});
      setSelectedPlots([]);
      clearPersistentState([`uiTracks-${eventId}`, `selectedPlots-${eventId}`,`viewTrack-${eventId}`,`trackIndex-${eventId}`]); // clean localStorage
      //Invalidate the cache for event data
      queryClient.invalidateQueries({ queryKey: ["eventData", eventId] });

      navigate("/event-page");
      alert("Event closed and data saved successfully!");
    },

    onError: (error: Error) => {
      console.error("Error closing the event:", error);
      alert(`Failed to close the event: ${error.message}`);
    },
  });
 // Mutation for creating a track
 const getRecommendationMutation = useMutation<Plot[], Error,{selectedPlots: Plot[], eventId : string | undefined, recommendationType : string}>({
  mutationFn: getRecommendation,
  onSuccess: (data: Plot[]) => {
    console.log("data", data)
    setSelectedPlots(data)
    console.log("got recommendation successfully");
  },
  onError: (error: Error) => {
    console.error("Error creating track:", error);
    alert(`Failed to calc recommedation: ${error.message}`);
  },
});
return {
  createTrack: createTrackMutation.mutate,

  closeEvent: closeEventMutation.mutate,

  getRecommendation: getRecommendationMutation.mutate,
  isGettingRecommendation: getRecommendationMutation.status === 'pending',
};

};
