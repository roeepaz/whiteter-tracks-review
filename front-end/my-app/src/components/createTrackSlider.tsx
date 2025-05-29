import React, { useState, useEffect } from "react";
import Slider from "@mui/material/Slider";
import "../styles/componentsStyles/modal.css";

interface TrackSliderModalProps {
  isOpen: boolean;
  //onClose: () => void;
  onSubmit: (value: number) => void;
}

const CreateTrackSlider: React.FC<TrackSliderModalProps> = ({ isOpen, onSubmit }) => {
  const [sliderValue, setSliderValue] = useState<number>(0);

  const handleSubmit = () => {
    onSubmit(sliderValue); // Pass the slider value back to the parent
  };

  const handleSliderChange = (event: Event, newValue: number | number[]) => {
    setSliderValue(newValue as number);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    if (value === "" || (Number(value) >= 0 && Number(value) <= 1)) {
      setSliderValue(Number(value));
    }
  };

  return (
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div className="slider-container">
          <Slider
            value={sliderValue}
            onChange={handleSliderChange}
            min={0}
            max={1}
            step={0.01}
            valueLabelDisplay="off"
            aria-labelledby="time-slider"
          />
          <div className="input-container">
            <label htmlFor="slider-input">Enter Value (0 to 1):</label>
            <input
              id="slider-input"
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={sliderValue.toString()}
              onChange={handleInputChange}
            />
          <div className="modal-buttons">
            <button className="modal-save-button" onClick={handleSubmit} >
              Create Track
            </button>
           
          </div>
          </div>
        </div>
      </div>    
  );
};

export default CreateTrackSlider;
