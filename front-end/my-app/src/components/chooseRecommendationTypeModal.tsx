import React, { useState, useEffect } from "react";
import Modal from "react-modal";
import "../styles/componentsStyles/modal.css";

interface ChooseRecommendationTypeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (selectedType: string) => void;
  config: any
}

const ChooseRecommendationTypeModal: React.FC<ChooseRecommendationTypeModalProps> = ({
  isOpen,
  onClose,
  onSubmit, // Receive the function
  config,
}) => { 
    const [ recommendationTypes, setRecommendationTypes] = useState<string[]>([]);
  
   useEffect(() => {
      if (config?.RECOMMENDATIONS_NAMES) {
        setRecommendationTypes(config.RECOMMENDATIONS_NAMES);
      } 
    }, [config]);
  const [selectedType, setSelectedType] = useState<string>("");


  const handleRadioChange = (reco: string) => {
    setSelectedType(reco);
  };

  const handleSave = () => {
    if (selectedType) {
      onSubmit(selectedType); //  Submit selected type
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      contentLabel="Choose Recommendation Type"
      className="event-modal-content"
      overlayClassName="event-modal-overlay"
    >
      <h3 className="modal-title">Choose Recommendation Type</h3>
      <p className="modal-text">the default is by trackId</p>

      <div className="modal-radio-group">
        {recommendationTypes.map((reco, index) => (
          <label key={index} className="modal-radio-label">
            <input
              type="radio"
              name="recommendationType"
              value={reco}
              checked={selectedType === reco}
              onChange={() => handleRadioChange(reco)}
            />
            {reco}
          </label>
        ))}
      </div>

      <div className="modal-buttons">
        <button className="modal-save-button" onClick={handleSave} disabled={!selectedType}>
          Save
        </button>
        <button className="modal-cancel-button" onClick={onClose}>
          Cancel
        </button>
      </div>
    </Modal>
  );
};

export default ChooseRecommendationTypeModal;
