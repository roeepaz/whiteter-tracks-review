import { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchEventPlots, fetchConfig } from "../API/apiServer";
import { Plot, DictData, TrackPlot, TrackAndPlotsConnection, UsePlotsResult } from "../type/types";
import { getColor } from "../utils/colors";
import { EventDataKey } from "../constants/eventDataKeys";
import { markPerf } from "../utils/perfUtils";
interface ProcessedData {
  unassociatedPlots: Plot[];
  associatedPlots: Plot[];
  sensorsTracksColors: { [key: number]: [number, number, number] };
  STNColors: { [key: number]: { [key: number]: [number, number, number] } };
  plotsWithoutTrack_id: Plot[];
}

const processPlotData = (
  rawPlots: Plot[],
  rawConnection: TrackAndPlotsConnection[]
): ProcessedData => {
  const uniqueTracks = [...new Set(rawPlots.map((plot) => plot.track_id))];
  const uniqueSensors = [...new Set(rawPlots.map((plot) => plot.system_id))];

  const plotsWithoutTrack_id = rawPlots.filter((plot) => plot.track_id === -1);
  const plotsWithoutTrack_idSet = new Set(plotsWithoutTrack_id.map((p) => p.plot_id));

  // 🔧 שיפור חשוב נוסף: הפוך את rawConnection ל-Set
  const connectionPlotIdSet = new Set(rawConnection.map((c) => c.plot_id));

  const sensorsTracksColors = uniqueTracks.reduce((acc, track) => {
    acc[track] = getColor();
    return acc;
  }, {} as { [key: number]: [number, number, number] });

  const STNColors = uniqueSensors.reduce((acc, sensor) => {
    const stns = [
      ...new Set(rawPlots.filter((plot) => plot.system_id === sensor).map((plot) => plot.STN)),
    ];
    acc[sensor] = stns.reduce((stnAcc, stn) => {
      stnAcc[stn] = getColor();
      return stnAcc;
    }, {} as { [key: number]: [number, number, number] });
    return acc;
  }, {} as { [key: number]: { [key: number]: [number, number, number] } });

  const plotsWithColors: Plot[] = rawPlots.map((plot) => ({
    ...plot,
    track_color: !plotsWithoutTrack_idSet.has(plot.plot_id)
      ? sensorsTracksColors[plot.track_id]
      : [255, 140, 0],
    STN_color: STNColors[plot.system_id]?.[plot.STN],
    is_associate: connectionPlotIdSet.has(plot.plot_id), // ✅ כאן המהירות עלתה משמעותית
  }));

  const unassociatedPlots = plotsWithColors.filter((plot) => !plot.is_associate);
  const associatedPlots = plotsWithColors.filter((plot) => plot.is_associate);

  return {
    unassociatedPlots,
    associatedPlots,
    sensorsTracksColors,
    STNColors,
    plotsWithoutTrack_id,
  };
};

export const usePlots = (
  eventId: string | undefined,
  selectedPlots: Plot[],
): UsePlotsResult => {
  const [plots, setPlots] = useState<Plot[]>([]);
  const [existTracksPlots, setExistTracksPlots] = useState<TrackPlot[]>([]);
  const [tracksIDs, setTracksIDs] = useState<number[]>([]);
  const [filteredPlots, setFilteredPlots] = useState<Plot[]>([]);
  const [filteredPlotsByTime2, setFilteredPlotsByTime] = useState<Plot[]>([]);
  const [filteredSelectedPlots, setFilteredSelectedPlots] = useState<Plot[]>([]);
  const [maxTime, setMaxTime] = useState<number>(0);
  const [plotsAroundToHalo, setPlotsAroundTohalo] = useState<Plot[]>([]);
  const [plotsAssociateToTrack, setPlotsAssociateToTrack] = useState<Plot[]>([]);
  const [connections, setConnections] = useState<TrackAndPlotsConnection[]>([]);
  const [plotsWithoutTrack_id, setPlotsWithoutTrack_id] = useState<Plot[]>([]);
  const [sensors, setSensors] = useState<number[]>([]);

  // Fetch data
  const { data, isLoading, isError, refetch } = useQuery<DictData>({
    queryKey: ["eventData", eventId],
    queryFn: () => fetchEventPlots(eventId),
    enabled: !!eventId,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });

  const { data: config, isError: isErrorConfig } = useQuery({
    queryKey: ['config'],
    queryFn: fetchConfig,
    staleTime: 24 * 60 * 60 * 1000,
  });

  // Memoized processing of raw data
  const processed = useMemo(() => {
    if (!data || !Array.isArray(data[EventDataKey.PLOTS])) return null;
    const rawPlots = data[EventDataKey.PLOTS] as Plot[];
    const rawConnection = data[EventDataKey.CORRELATIONS] || [];
    setConnections(rawConnection); // still needed outside processPlotData

    markPerf('T4_PROCESSING_START', { plotCount: rawPlots.length });
    const result = processPlotData(rawPlots, rawConnection);
    markPerf('T5_PROCESSING_COMPLETE', { plotCount: rawPlots.length });

    return {
      ...result,
      rawPlots,
      tracks: data[EventDataKey.WHITE_TRACKS] || [],
    };
  }, [data]);

  // Populate states from processed data
  useEffect(() => {
    if (!processed) return;

    const {
      unassociatedPlots,
      associatedPlots,
      plotsWithoutTrack_id,
      rawPlots,
      tracks,
    } = processed;

    setPlots(unassociatedPlots);
    setFilteredPlots(unassociatedPlots);
    setPlotsAssociateToTrack(associatedPlots);
    setPlotsWithoutTrack_id(plotsWithoutTrack_id);
    setExistTracksPlots(tracks);
    const maxTime = rawPlots.reduce((max, p) => Math.max(max, p.t), -Infinity);
    setMaxTime(maxTime);
    setSensors([...new Set(rawPlots.map((p) => p.system_id))]);
    setTracksIDs([...new Set(tracks.map((p) => p.id))]);
  }, [processed]);

  // Time-based filtering
  const filterPlotsByTime = (time: number) => {
    setFilteredPlotsByTime(filteredPlots.filter((plot) => plot.t <= time));
    setFilteredSelectedPlots(selectedPlots.filter((plot) => plot.t <= time));
  };

  const getFillColor = (plot: Plot, paintState: number): [number, number, number] => {
    switch (paintState) {
      case 1:
        return plot.track_color || [255, 140, 0];
      case 2:
        return plot.STN_color || [255, 140, 0];
      default:
        return [255, 140, 0];
    }
  };

  return {
    plots,
    existTracksPlots,
    tracksIDs,
    filteredPlots,
    setFilteredPlots,
    setFilteredPlotsByTime,
    filteredSelectedPlots,
    setFilteredSelectedPlots,
    sensors,
    maxTime,
    plotsAroundToHalo,
    setPlotsAroundTohalo,
    plotsAssociateToTrack,
    plotsWithoutTrack_id: plotsWithoutTrack_id,
    connections,
    getFillColor,
    isLoading,
    isError,
    refetch,
    config,
    isErrorConfig,
  };
};
