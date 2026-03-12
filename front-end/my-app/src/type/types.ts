// src/types.ts
import { ViewState as MapViewState } from "react-map-gl";

// Define the structure of a Plot
export interface Plot {
    system_id : number;
    STN : number;
    plot_id : number;
    t : number;
    x : number;
    y : number;
    z : number;
    sig_x : number;
    sig_y : number;
    sig_z : number;
    target_id : number;
    latitude : number;
    longitude : number;
    altitude : number;
    track_id : number;
    track_color: [number,number, number];
    STN_color: [number,number, number];
    is_associate: boolean;
  }
  export interface TrackPlot {
    latitude : number;
    longitude : number;
    altitude : number;
    id : number;
    time : number;
    
  }
  
  export type HoverInfo = {
    longitude: number;
    latitude: number;
    altitude: number;
    t: number;
    screenX: number;
    screenY: number;
    is_associate: boolean;
    target_id: number;
  } | null;
  
 export type Segment = {
    source: [number, number, number];
      target: [number, number, number];
  }
  
  // You can also define other types or enums
  export interface Event {
    id: string;
  }
  
  export type EventId = string | number;

  export interface CustomViewState extends MapViewState {
    pitch: number;
    bearing: number;
    padding: {
      top: number;
      bottom: number;
      left: number;
      right: number;
    };
    maxPitch?: number; // Optional max pitch
    minPitch?: number; // Optional min pitch
    }

    export interface TrackData {
      splinePoints: TrackPlot[];
      selectedPlots: Plot[];
      trackNote: string | null;
    }
    export interface BackendResponse {
      success: boolean;
      message: string;
    }
    export interface TrackAndPlotsConnection {
      white_track_id: number;
      plot_id: number;
      system_id: number;
    }
    export interface DictData{
      1 : Plot[];
      2 : TrackPlot[];
      3: TrackAndPlotsConnection [];
    }
    export type MapControlsProps = {
      increasePitch: () => void;
      decreasePitch: () => void;
      increaseBearing: () => void;
      decreaseBearing: () => void;
      resetLook: () => void;
      handleCreateTrack: () => void;
      handleTrackSubmit: () => void;
      clearSelectedPlots: () => void;
      handleCloseEvent: () => void;
    };
    export type ButtonConfig = {
      label: string;
      onClick: (parameter?: any) => void; // Accepts an optional parameter
      className?: string;
      disabled?: boolean; 
      tooltip?: string;

    };

    export type PickInfo<T> = {
      object: T | null; // The clicked object (or null if no object was clicked)
      index: number; // Index of the object in the data array
      coordinate?: [number, number, number]; // World coordinates of the click
      x: number; // Screen X coordinate
      y: number; // Screen Y coordinate
    };
    import { UseQueryResult } from "@tanstack/react-query";

    export interface UsePlotsResult {
      plots: Plot[];
      existTracksPlots: TrackPlot[];
      tracksIDs: number[];
      filteredPlots: Plot[];
      setFilteredPlots: React.Dispatch<React.SetStateAction<Plot[]>>;
      setFilteredPlotsByTime: React.Dispatch<React.SetStateAction<Plot[]>>;
      filteredSelectedPlots: Plot[];  
      setFilteredSelectedPlots: React.Dispatch<React.SetStateAction<Plot[]>>;
      sensors : number [];
      maxTime: number;
      plotsAroundToHalo: Plot[];
      setPlotsAroundTohalo: React.Dispatch<React.SetStateAction<Plot[]>>;
      plotsAssociateToTrack: Plot[];
      plotsWithoutTrack_id: Plot[];
      connections: TrackAndPlotsConnection[];
      getFillColor: (plot: Plot, paintState: number) => [number, number, number];
      isLoading: boolean;
      isError: boolean;
      refetch: () => Promise<UseQueryResult<any, Error>>;
      config: any,
      isErrorConfig: boolean,
    }