import React, { useState, useEffect } from "react";
import { useQuery } from '@tanstack/react-query';
import Modal from "react-modal";
import { fetchConfig } from "../API/apiServer";
import '../styles/componentsStyles/modal.css';

interface CreateTrackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (selectedOption: string ) => void;
  config: any;
}

const CreateTrackModal: React.FC<CreateTrackModalProps> = ({ isOpen, onClose, onSubmit, config }) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null); // Default to no selection
  const [options, setOptions] = useState<string[]>([])

  useEffect(() => {
    if (config?.TAGS_FOR_WHITE_TRACK) {
      setOptions(config.TAGS_FOR_WHITE_TRACK);
    } 
  }, [config]);

  const handleSave = () => {
    onSubmit(selectedOption || "");
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
      <h3 className="modal-title">save the track</h3>
      <p className="modal-text">Please select an option for this track:</p>
      <select
        value={selectedOption || ""}
        onChange={(e) => setSelectedOption(e.target.value || null)}
        className="modal-dropdown"
      >
        <option value="">-- Select an option --</option> {/* Default unselected option */}
        {options.map((option, index) => (
          <option key={index} value={option}>
            {option}
          </option>
        ))}
      </select>
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

export default CreateTrackModal;
