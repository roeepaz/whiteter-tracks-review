import { useState, useEffect, useCallback } from "react";
import { LinearInterpolator } from "@deck.gl/core";
import { CustomViewState } from "../type/types"; // ודא שהטיפוס CustomViewState מוגדר

const initialViewState: CustomViewState = {
  longitude: 34.469916,
  latitude: 31.537530, 
  zoom: 10,
  pitch: 45,
  bearing: 0,
  padding: { top: 0, bottom: 0, left: 0, right: 0 },
  maxPitch: 85,
};

export const useMapViewState = () => {
  const [viewState, setViewState] = useState<CustomViewState>(initialViewState);
  const [keyPressed, setKeyPressed] = useState("");

  // Functions to modify viewState
  const increasePitch = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      pitch: Math.min(prev.pitch + 5, 85),
      transitionInterpolator: new LinearInterpolator(["pitch"]),
      transitionDuration: 500,
    }));
  }, []);

  const decreasePitch = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      pitch: Math.max(prev.pitch - 10, 0),
      transitionInterpolator: new LinearInterpolator(["pitch"]),
      transitionDuration: 500,
    }));
  }, []);

  const increaseBearing = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      bearing: (prev.bearing + 10) % 360,
      transitionInterpolator: new LinearInterpolator(["bearing"]),
      transitionDuration: 500,
    }));
  }, []);

  const decreaseBearing = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      bearing: (prev.bearing - 10 + 360) % 360,
      transitionInterpolator: new LinearInterpolator(["bearing"]),
      transitionDuration: 500,
    }));
  }, []);

  const resetLook = useCallback(() => {
    setViewState((prev) => ({
      ...initialViewState,
      transitionInterpolator: new LinearInterpolator(["pitch", "bearing"]),
      transitionDuration: 500,
    }));
  }, []);

const zoomIn = () => {
  setViewState((prevState) => ({
    ...prevState,
    zoom: prevState.zoom + 0.2, // Increment zoom level
  }));
};

const zoomOut = () => {
  setViewState((prevState) => ({
    ...prevState,
    zoom: prevState.zoom - 0.2, // Decrement zoom level
  }));
};


  // Event listener for keyboard controls
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      setKeyPressed(event.key);
      switch (event.key) {
        case "ArrowUp":
          decreasePitch();
          break;
        case "ArrowDown":
          increasePitch();
          break;
        case "ArrowRight":
          decreaseBearing();
          break;
        case "ArrowLeft":
          increaseBearing();
          break;
        default:
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [decreasePitch, increasePitch, decreaseBearing, increaseBearing]);

  const handleViewStateChange = useCallback(
    (params: { viewState: CustomViewState }) => {
      const { viewState } = params;
      setViewState((prevState) => ({
        ...prevState,
        ...viewState,
      }));
    },
    []
  );

  return {
    viewState,
    keyPressed,
    setViewState,
    increasePitch,
    decreasePitch,
    increaseBearing,
    decreaseBearing,
    resetLook,
    handleViewStateChange,
    zoomIn,
    zoomOut
  };
};
