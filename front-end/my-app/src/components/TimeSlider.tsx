import React from "react";
import Slider from "@mui/material/Slider";
import "../styles/slider.css";

interface TimeSliderProps {
  time: number; // The current time value
  maxTime: number; // The maximum value for the slider
  onTimeChange: (newValue: number) => void; // Callback function to update time
}

const TimeSlider: React.FC<TimeSliderProps> = ({ time, maxTime, onTimeChange }) => {
  return (
    <div className="bottom-controls">
    <div className="slider-container">
      <p className="time-label">Time: {time.toFixed(1)}</p>
      <Slider
        value={time}
        onChange={(event, newValue) => {
          onTimeChange(newValue as number); // Pass the new value back to the parent
        }}
        min={0}
        max={maxTime}
        step={0.1}
        valueLabelDisplay="off" /* Disable default label on the slider handle */
        aria-labelledby="time-slider"
      />
    </div>
    </div>
  );
};

export default TimeSlider;
