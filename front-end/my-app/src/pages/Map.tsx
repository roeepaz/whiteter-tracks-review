import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import DeckGL from "@deck.gl/react";
import { Map as MapGL} from "react-map-gl";
import { PointCloudLayer, LineLayer } from "@deck.gl/layers";
import "mapbox-gl/dist/mapbox-gl.css";
//costom hooks
import { usePlots } from '../hooks/usePlots';
import { useMapViewState } from "../hooks/useMapViewState";
import { useSplineSegments } from "../hooks/useSplineSegments";
import { useTracks } from "../hooks/useTracks";
import { useTrackMutations } from "../hooks/useTrackMutations";
import { usePersistentState, clearPersistentState  } from '../hooks/usePersistentState';
// performance instrumentation
import { markPerf, printSummary, PERF_MODE } from '../utils/perfUtils';
//components that added on the map
import Button from '../components/Button';
import EventNotesModal from "../components/CloseEventNotesModal";
import SaveTrackModal from "../components/saveTrackModal";
import TimeSlider from "../components/TimeSlider";
import Sidebar from "../components/Sidebar";
import HoverInfo from "../components/HoverInfo";
import CreateTrackSlider from '../components/createTrackSlider';
import ChooseRecommendationTypeModal from '../components/chooseRecommendationTypeModal';
import FPSCounter from '../components/FPSCounter';
//types
import { Plot,HoverInfo as HoverInfoType, Segment ,TrackData, ButtonConfig} from "../type/types";
import Modal from "react-modal";
// css
import '../styles/base.css';
import '../styles/layout.css';
import '../styles/utilities.css';
import '../styles/componentsStyles/map.css';
import '../styles/errorsAndLoader.css'

Modal.setAppElement("#root"); // Bind modal to the root element for accessibility

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

const DOUBLE_CLICK_DELAY = 300; // Adjust delay as needed
let clickTimeout: ReturnType<typeof setTimeout> | null = null;

const Map: React.FC = () => {
  //the event id, got from the URL 
  const { eventId } = useParams<{ eventId: string }>(); // Get the eventId from the URL and enforce that it's a string
  //the current time of the time slider
  const [time, setTime] = useState(0); // Start time at 0
  //the plot hover (one in a time)
  const [hoverInfo, setHoverInfo] = useState<HoverInfoType>(null);

  const [UiTracks, setUiTracks] = usePersistentState<Record<number, TrackData>>(`uiTracks-${eventId}`, {});
  const [selectedPlots, setSelectedPlots] = usePersistentState<Plot[]>(`selectedPlots-${eventId}`, []); //index to the tracks id (above)
  
  const [trackIndex, setTrackIndex] =  usePersistentState<number>(`trackIndex-${eventId}`, 0); 
  //paint state: the numbers represent the secision by the user- 1 by track id, 2 by STN, 0 nether
  const [paintState, setPaintState] = useState<number>(0)

  //Enabled or unenabled the close event butten
  const [isCloseEventEnabled, setIsCloseEventEnabled] = useState<boolean>(false);
 
  const [isSubmitTrackEnable, setIsSubmitTrackEnable] = useState<boolean>(false);
   //notes for this event, user can edit as long as he work on the evnt
   const [eventNotes, setEventNotes] = useState<number []>([]);

  const [isCreateTrackOpen,setIsCreateTrackOpen] = useState<boolean> (false);
  const [recommendationType,setRecommendationType] = useState<string>('dbscan');
  const perfRenderedRef = useRef(false); // Track if perf T_END has fired for this event load

  const { plots,existTracksPlots,tracksIDs,
          filteredPlots, setFilteredPlots, setFilteredPlotsByTime, filteredSelectedPlots,
          setFilteredSelectedPlots,sensors,maxTime, 
          plotsAroundToHalo, setPlotsAroundTohalo,plotsAssociateToTrack,
          plotsWithoutTrack_id,connections, getFillColor,
          isLoading, isError, refetch, config,isErrorConfig       
    } = usePlots(eventId, selectedPlots);

  const {viewState,resetLook,handleViewStateChange, zoomIn, zoomOut} = useMapViewState();
  const {
    tracksToSee,tracksToSeeByTime,viewTrack,viewTrackByTime,
    setTracksToSeeByTime,setViewTrack,setViewTrackByTime,handleSeeTrack,handleSeeUiTrack,editUiTrack, updateFilteredPlotsForUiTracks
  } = useTracks(eventId,existTracksPlots, UiTracks, time,connections, plots, plotsAssociateToTrack, setTrackIndex,setUiTracks, setSelectedPlots, setFilteredPlots);

const { createTrack, closeEvent, getRecommendation,isGettingRecommendation } = useTrackMutations({
  setViewTrack,
  setUiTracks,
  setSelectedPlots,
  UiTracks,
  eventNotes,
  eventId,
  recommendationType
});

  const { combinedSplineData } = useSplineSegments(tracksToSeeByTime, viewTrackByTime);
  //the notes modal visiblelity
  const [isNotesModalOpen, setIsNoteModalOpen] = useState(false);
  const [isSaveTrackModalOpen, setIsSaveTrackModalOpen] = useState(false);
  const [isChooseRecommendationTypeModaOpen, setIsChooseRecommendationTypeModaOpen] = useState(false);
  const [showComment, setShowComment] = useState(true); // Controls visibility of the comment

  const handleSubmitNotes = (notes: number []) => {
    setEventNotes(notes);
    closeEvent(); 
  };

  const handleTimeChange = (newTime: number) => {
    setFilteredPlotsByTime(filteredPlots.filter((plot) => plot.t <= newTime));
    setFilteredSelectedPlots(selectedPlots.filter((plot) => plot.t <= newTime));

    setTime(newTime); // Update the local state
    //filterPlotsByTime(newTime); // Update the filtered plots
  };
  const filteredPlotsByTime = useMemo(
    () => filteredPlots.filter((plot) => plot.t <= time),
    [filteredPlots, time]
  );
  
  
  useEffect(() => {
    setIsCloseEventEnabled(() => {
      return Object.keys(UiTracks).length > 0;  // Check if UiTracks has any keys
    });
  }, [UiTracks]);
  
  useEffect(() => {
    setIsCreateTrackOpen(selectedPlots.length >=4)
    setFilteredSelectedPlots(selectedPlots.filter((plot)=> plot.t <= time))
  }, [selectedPlots])
  
  useEffect(() => {
    setTracksToSeeByTime(tracksToSee.filter((track) => track.time <= time))
    setViewTrackByTime(viewTrack.filter((plot) => plot.time <= time))
    setIsSubmitTrackEnable(viewTrack.length >0);
  },[time, tracksToSee, viewTrack])

  const handlePlotDoubleClick = (clickedPlot : Plot) => {
      switch(paintState){
        //by track_id
        case 1:
          if( clickedPlot.track_id !== -1)
            setPlotsAroundTohalo(plots.filter((plot) => plot.track_id === clickedPlot.track_id))
          else
            setPlotsAroundTohalo(plotsWithoutTrack_id)
          break
        // by stn
        case 2:
          const plotsBySensorOnly : Plot[] = plots.filter((plot) => plot.system_id === clickedPlot.system_id);
          setPlotsAroundTohalo((prev) => {
            const x = plotsBySensorOnly.filter((plot) => plot.STN === clickedPlot.STN);
            return [...prev, ...x]
          });
      }
  };
  const handlePlotClick = (info: any, event: any) => {
    if (info.object) {
      const clickedPlot : Plot = info.object;
      if(clickTimeout){
        // If a timeout is already set, it's a double click
        clearTimeout(clickTimeout);
        clickTimeout = null;
        handlePlotDoubleClick(clickedPlot); // Trigger double-click action
      }
      else {
        // Set a timeout for a single click
        clickTimeout = setTimeout(() => {
          let is_associate_to_ui_track = false;
  
          // Iterate over all tracks and check if clicked plot is part of any track
          Object.values(UiTracks).forEach(track => {
            if (
              track.selectedPlots.some(
                plot => plot.plot_id === clickedPlot.plot_id
              )
            ) {
              is_associate_to_ui_track = true;
            }
          });
  
            if(clickedPlot.is_associate || is_associate_to_ui_track)
            {
              alert('Opps this plot is associated to an track')     
            }
            else{
              setSelectedPlots((prevSelected) => {
                const isAlreadySelected = prevSelected.includes(clickedPlot);
                if (!isAlreadySelected) {
                  return [...prevSelected, clickedPlot];
                } else {
                  return prevSelected.filter((plot) => !(plot.plot_id === clickedPlot.plot_id && plot.system_id === clickedPlot.system_id));
                }
              });
            }
          clickTimeout = null;
        }, DOUBLE_CLICK_DELAY);
      }
    }
  };

  const changePaintState = (num: number) => {    
    console.log(num)
   setPaintState(num);
  };

  const handleCteateTrack = (smoothingFactor : number) => {
    if (selectedPlots.length >= 4) {
      createTrack({ selectedPlots, smoothingFactor });
    } else {
      alert("please select at least four plots");
    }
  };
  
  const handleTrackSubmit = (notes : string) => {
    if (viewTrack.length) {
      const splinePoints = viewTrack.map((plot) => ({
        ...plot,
        id: trackIndex, 
      }));
      // Create a new track object
      const newTrack: TrackData = {
        splinePoints: splinePoints,
        selectedPlots: selectedPlots,
        trackNote: notes === "" ? null : notes,
      }; 
      // Add the new track to tracks
      setUiTracks((prev: Record<number, TrackData>) => ({
        ...prev,
        [trackIndex]: newTrack, // Use trackIndex as the key
      }));
        
     // Remove plots of the new track from filteredPlots
    setFilteredPlots((prev) =>
      prev.filter(
        (plot) =>
          !selectedPlots.some(
            (newTrackPlot) => newTrackPlot.plot_id === plot.plot_id
          )
      )
    );
      // Increment the track index for the next track
      setTrackIndex((prevIndex) => prevIndex + 1);
      setViewTrack([]);
      setSelectedPlots([]);
    } else {
      alert("No track selected");
    }
  };
  
  
  const clearSelectedPlots = () => {
    setSelectedPlots([]);
    setViewTrack([]);
    setPlotsAroundTohalo([])
  };
  
  // Define the layers, recalculated when plots(for the first time), selectedPlots, time selected change
  const layers = useMemo(() => {
    markPerf('T6_RENDER_START', { plotCount: filteredPlotsByTime.length });
    const result = [
      new PointCloudLayer<Plot>({
        id: "point-cloud-layer",
        data: [...filteredPlotsByTime],
        pickable: true,
        getPosition: (d: Plot) => [d.longitude, d.latitude, d.altitude],
        getColor: (d: Plot) => getFillColor(d, paintState),
        onClick: handlePlotClick, 
      
        pointSize: 2,
        //material: defaultMaterial, // Default material
        onHover: (info) => {
          if (info.object) {
            setHoverInfo({
              longitude: info.object.longitude,
              latitude: info.object.latitude,
              altitude: info.object.altitude,
              t : info.object.t,
              is_associate : info.object.is_associate,
              target_id : info.object.target_id,
              screenX: info.x,
              screenY: info.y,
            });
          } else {
            setHoverInfo(null); // Clear hover info when not hovering over a point
          }
        },
      }),
    ];
    markPerf('T7_LAYERS_CONSTRUCTED', { plotCount: filteredPlotsByTime.length });
    return result;
  }, [plots, paintState, filteredPlots, filteredPlotsByTime]);

  const selectedLayer = useMemo(() => {
    return [
      new PointCloudLayer<Plot>({
        id: "selected-layer",
        data: [...filteredSelectedPlots, ...plotsAroundToHalo],
        pickable: true,
        getPosition: (d: Plot) => [d.longitude, d.latitude, d.altitude],
        //getColor: (d: Plot) => getFillColor(d),
        getColor: [255,200,0, 100],
        onClick: handlePlotClick, 
        //material: haloMaterial,
        pointSize: 5,
        onHover: (info) => {
          if (info.object) {
            setHoverInfo({
              longitude: info.object.longitude,
              latitude: info.object.latitude,
              altitude: info.object.altitude,
              t : info.object.t,
              is_associate : info.object.is_associate,
              target_id: info.object.target_id,
              screenX: info.x,
              screenY: info.y,
            });
          } else {
            setHoverInfo(null); // Clear hover info when not hovering over a point
          }
        },
      }),
    ];
  }, [selectedPlots, filteredSelectedPlots, plotsAroundToHalo]);

  const lineLayer = useMemo(() => {
    //console.log("all tracks", combinedSplineData);
    return [
      new LineLayer({
        id: "spline-line-layer",
        data: combinedSplineData,
        getSourcePosition: (d: Segment) => d.source,
        getTargetPosition: (d : Segment) => d.target,
        getColor: [0, 128, 255],
        widthScale: 0.5,
        widthMinPixels: 0.5,
        pointSize: 5 // Size in pixel
      }),
    ];
  }, [combinedSplineData]);
  
  if (isLoading) {
    return (
      <div className="full-page-loader">
        <div className="spinner"></div>
        <h1>Loading Plots...</h1>
      </div>
    );
  }
  
  if (isError) {
    return (
      <div className="error-container">
        <div className="error-img">
        </div>
        <h1>Oops! Something went wrong</h1>
        <h1>Error fetching plots</h1>

        <button onClick={() => refetch()}>Retry</button> {/* Retry button */}
      </div>
    );
  } 
  
  if (isErrorConfig) {
    return (
      <div className="error-container">
        <div className="error-img">
        </div>
        <h1>Oops! Something went wrong</h1>
        <h1>Error fetching app config</h1>

        <button onClick={() => refetch()}>Retry</button> {/* Retry button */}
      </div>
    );
  } 
  
  
  const mapButtons: ButtonConfig[] = [
    { label: 'Reset look', onClick: resetLook },
    { label: 'Zoom In', onClick: zoomIn }, // Zoom In button
    { label: 'Zoom Out', onClick: zoomOut }, // Zoom Out button
  ];
  const controlButtons: ButtonConfig[] = [
    { label: 'save the track', onClick: (() => setIsSaveTrackModalOpen(true)), className: "save-button",disabled: !isSubmitTrackEnable},
    { 
      label: 'Close Event', 
      onClick: (()=> setIsNoteModalOpen(true)), 
      className: "close-button", 
      disabled: !isCloseEventEnabled,
      tooltip: "to close the event you need to create at list one track"
    },  
    { 
      label: isGettingRecommendation ? "Loading..." : "Get Recommendation",
      onClick: () => {
        if (selectedPlots.length === 0) {
          alert("Please select at least one plot to get recommendation");
          return;
        }
        getRecommendation({ selectedPlots, eventId, recommendationType });
      },      
      className: "get-recommendation-button", 
      disabled: isGettingRecommendation
      //tooltip: "to close the event you need to create at list one track"
    },  
    { label: 'clear', onClick: clearSelectedPlots , className: "clear-button", },
    { label: 'Choose recommendation type', onClick: (() => setIsChooseRecommendationTypeModaOpen(true)), className: "save-button"},
  ];
  
  return (
    <div className="map-container">
      {/* Row for mapButtons */}
      <div className="top-controls">
      {mapButtons.map((button, index) => (
        <Button
          key={index}
          label={button.label}
          onClick={button.onClick}
          className={button.className}
          disabled={button.disabled}
        />
      ))}
        <EventNotesModal
              isOpen={isNotesModalOpen}
              onClose={() => setIsNoteModalOpen(false)}
              onSubmit={handleSubmitNotes}
              sensors={sensors}
            />
        <SaveTrackModal
          isOpen={isSaveTrackModalOpen}
          onClose={() => setIsSaveTrackModalOpen(false)}
          onSubmit={handleTrackSubmit}
          config={config}
        />
          <ChooseRecommendationTypeModal
          isOpen={isChooseRecommendationTypeModaOpen}
          onClose={() => setIsChooseRecommendationTypeModaOpen(false)}
          onSubmit={(type) => setRecommendationType(type)} //  Pass a function that receives the selected type
          config={config}
        />

      </div>

       {/* Left Column: Control Buttons */}
    <div className="left-controls">
      {controlButtons.map((button, index) => (
        <Button
          key={index}
          label={button.label}
          onClick={button.onClick}
          className={button.className}
          disabled={button.disabled}
        />
      ))}
    </div>

    {/* Right Corner: Create Track Slider */}
    {isCreateTrackOpen && (
      <div className="create-track-slider">
        <CreateTrackSlider
          isOpen={isCreateTrackOpen}
          onSubmit={handleCteateTrack}
        />
      </div>
    )}

      <DeckGL
        initialViewState={viewState}
        controller={{
          scrollZoom: { smooth: true, speed: 0.5 }, // Enables smooth zoom with mouse scroll
          dragPan: true, // Enables panning with the mouse drag
          dragRotate:  true, // You can set this to true if you want rotation on right-click drag
          doubleClickZoom: false, // Optional: enables zoom on double-click
          keyboard: false,
          // Enable panning with the middle mouse button (button: 1)        
        }}
        layers={[layers, lineLayer, selectedLayer]}
        //effects={[lightingEffect]}
        //viewState={viewState}  // Bind the view state to DeckGL
        onViewStateChange={handleViewStateChange} // Update on map interaction
        onAfterRender={() => {
          // Fire only once per load cycle
          if (PERF_MODE && filteredPlotsByTime.length > 0 && !perfRenderedRef.current) {
            perfRenderedRef.current = true;
            markPerf('T_END_FIRST_RENDER', { plotCount: filteredPlotsByTime.length });
            printSummary();
          }
        }}
      >
        <MapGL
          mapboxAccessToken={MAPBOX_TOKEN}
          mapStyle="mapbox://styles/mapbox/dark-v10"
          style={{ width: "100%", height: "100%" }}
        />
        <HoverInfo hoverInfo={hoverInfo} />

        {showComment && (
        <div className="comment-box">
          <span>note that to create an track you need at least four plots</span>
          <button onClick={() => setShowComment(false)}>X</button>
        </div>
      )}
      </DeckGL>

      <Sidebar tracksIDs={tracksIDs} UiTracks={UiTracks} paintState={paintState} setPaintState={setPaintState} handleSeeTrack={handleSeeTrack} handleSeeUiTrack={handleSeeUiTrack} editUiTrack={editUiTrack} />

      <TimeSlider time={time} maxTime={maxTime} onTimeChange={handleTimeChange} />

      <FPSCounter />

    </div>
  );
};
export default Map;
