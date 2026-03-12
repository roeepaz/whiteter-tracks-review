import React, { useState } from "react";
import Modal from "react-modal";
import "../styles/componentsStyles/modal.css";

interface EventNotesModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (selectedSensors: number[]) => void; // Now submits an array of selected sensors
  sensors: number[]; // Array of available sensor options
}

const EventNotesModal: React.FC<EventNotesModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  sensors,
}) => {
  const [selectedSensors, setSelectedSensors] = useState<number[]>([]);

  const handleCheckboxChange = (sensor: number) => {
    setSelectedSensors((prevSelected) =>
      prevSelected.includes(sensor)
        ? prevSelected.filter((s) => s !== sensor) // Remove if already selected
        : [...prevSelected, sensor] // Add if not selected
    );
  };

  const handleSave = () => {
    onSubmit(selectedSensors);
    onClose(); // Close the modal after submitting
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      contentLabel="Event Selection"
      className="event-modal-content"
      overlayClassName="event-modal-overlay"
    >
      <h3 className="modal-title">Close Event</h3>
      <p className="modal-text">Please select which sensors were problematic.</p>
      
      <div className="modal-checkbox-group">
        {sensors.map((sensor, index) => (
          <label key={index} className="modal-checkbox-label">
            <input
              type="checkbox"
              value={sensor}
              checked={selectedSensors.includes(sensor)}
              onChange={() => handleCheckboxChange(sensor)}
            />
            {sensor}
          </label>
        ))}
      </div>

      <div className="modal-buttons">
        <button className="modal-save-button" onClick={handleSave}>
          Save
        </button>
        <button className="modal-cancel-button" onClick={onClose}>
          Cancel
        </button>
      </div>
    </Modal>
  );
};

export default EventNotesModal;
