import { useState, useEffect } from "react";
import { Plot, TrackPlot, TrackData, TrackAndPlotsConnection } from "../type/types";
import { usePersistentState} from '../hooks/usePersistentState';

export const useTracks = (
  eventId: string | undefined,
  existTracksPlots: TrackPlot[],
  UiTracks: Record<number, TrackData>,
  time: number,
  connections: TrackAndPlotsConnection[],
  plots: Plot[],
  plotsAssociateToTrack: Plot[],
  setTrackIndex: React.Dispatch<React.SetStateAction<number>>,
  setUiTracks: React.Dispatch<React.SetStateAction<Record<number, TrackData>>>,
  setSelectedPlots: React.Dispatch<React.SetStateAction<Plot[]>>,
  setFilteredPlots: React.Dispatch<React.SetStateAction<Plot[]>>
) => {
  // State variables
  const [tracksToSee, setTracksToSee] = useState<TrackPlot[]>([]);
  const [tracksToSeeByTime, setTracksToSeeByTime] = useState<TrackPlot[]>([]);
  const [viewTrack, setViewTrack] = usePersistentState<TrackPlot[]>(`viewTrack-${eventId}`, []);
  const [viewTrackByTime, setViewTrackByTime] = useState<TrackPlot[]>([]);

  // Update tracks based on time
  useEffect(() => {
    setTracksToSeeByTime(tracksToSee.filter((track) => track.time <= time));
    setViewTrackByTime(viewTrack.filter((plot) => plot.time <= time));
  }, [time, tracksToSee, viewTrack]);

  // Utility function to update filtered plots for UI tracks
  const updateFilteredPlotsForUiTracks = (
    prev: Plot[],
    isAlreadySelected: boolean,
    trackId: number
  ): Plot[] => {
    if (!isAlreadySelected) {
      const plotsToAdd = UiTracks[trackId]?.selectedPlots || [];
      return [...prev, ...plotsToAdd];
    } else {
      const selectedPlotsForTrack = UiTracks[trackId]?.selectedPlots || [];
      return prev.filter(
        (plot) => !selectedPlotsForTrack.some((selectedPlot) => selectedPlot.plot_id === plot.plot_id)
      );
    }
  };

  // Utility function to update filtered plots for past tracks
  const updateFilteredPlotsForPastTracks = (
    prev: Plot[],
    isAlreadySelected: boolean,
    trackId: number
  ): Plot[] => {
    if (!isAlreadySelected) {
      const associatedConnections = new Set(
        connections
          .filter((con) => con.white_track_id === trackId)
          .map((con) => `${con.plot_id}-${con.system_id}`) // Unique identifier
      );
    
      const plotsToAdd = plotsAssociateToTrack.filter(
        (plot) => associatedConnections.has(`${plot.plot_id}-${plot.system_id}`)
      );
    
      return [...prev, ...plotsToAdd];
    } else {
      const plotIdsToRemove = new Set(
        connections
          .filter((con) => con.white_track_id === trackId)
          .map((con) => con.plot_id)
      );
    
      return prev.filter((plot) => !plotIdsToRemove.has(plot.plot_id));
    }
    
  };

  // Handlers
  const handleSeeTrack = (trackId: number) => {
    const isAlreadySelected = tracksToSee.some((track) => track.id === trackId);
    setTracksToSee((prev) => {
      if (isAlreadySelected) {
        return prev.filter((track) => track.id !== trackId);
      } else {
        const selectedTrack = existTracksPlots.filter((plot) => plot.id === trackId);
        return [...prev, ...selectedTrack];
      }
    });
    setFilteredPlots((prev) =>
      updateFilteredPlotsForPastTracks(prev, isAlreadySelected, trackId)
    );
  };

  const handleSeeUiTrack = (trackId: number) => {
    const isAlreadySelected = tracksToSee.some((track) => track.id === trackId);
    setTracksToSee((prev) => {
      if (isAlreadySelected) {
        return prev.filter((track) => track.id !== trackId);
      } else {
        const selectedTrack = UiTracks[trackId]?.splinePoints || [];
        return [...prev, ...selectedTrack];
      }
    });
    setFilteredPlots((prev) =>
      updateFilteredPlotsForUiTracks(prev, isAlreadySelected, trackId)
    );
  };

  const editUiTrack = (trackId: number) => {
    const track = UiTracks[trackId];
    if (track) {
      setUiTracks((prevUiTracks) => {
        const updatedTracks = { ...prevUiTracks };
        delete updatedTracks[trackId];
        return updatedTracks;
      });
      setFilteredPlots((prev) => [...prev, ...track.selectedPlots])
      setSelectedPlots(track.selectedPlots);
      setViewTrack(track.splinePoints);
      setTracksToSee((prev) => prev.filter((track) => track.id !== trackId));
      setTrackIndex((prev) => prev - 1);
    }
  };

  return {
    tracksToSee,
    setTracksToSee,
    tracksToSeeByTime,
    setTracksToSeeByTime,
    viewTrack,
    setViewTrack,
    viewTrackByTime,
    setViewTrackByTime,
    handleSeeTrack,
    handleSeeUiTrack,
    editUiTrack,
    updateFilteredPlotsForUiTracks
  };
};
