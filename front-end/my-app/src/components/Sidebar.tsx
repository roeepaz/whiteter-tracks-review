import React, {useState} from "react";
import '../styles/componentsStyles/sidebar.css';

interface SidebarProps {
  //? do we need it? 
  //TODO if we do need it so add the STN's
  sensors?: number[]; // Array of sensor IDs
  tracksIDs: number[]; // Array of past track IDs
  UiTracks: Record<number, any>; // Object containing today's tracks
  paintState: number;
  setPaintState: React.Dispatch<React.SetStateAction<number>>;
  handleSeeTrack: (trackId: number) => void; // Callback to handle past track selection
  handleSeeUiTrack: (trackId: number) => void; // Callback to handle today's track selection
  editUiTrack: (trackId: number) => void; // Callback to handle today's track selection
}

const Sidebar: React.FC<SidebarProps> = ({
  tracksIDs,
  UiTracks,
  paintState,
  setPaintState,
  handleSeeTrack,
  handleSeeUiTrack,
  editUiTrack,
}) => {
  const [isTracksListVisible, setIsTracksListVisible] = useState(false);

  const toggleTracksList = () => {
    setIsTracksListVisible((prev) => !prev);
  };

  return (
    <div className="sidebar-container">
      <div className="sidebar">
               
      <div>
        Select the plots painting state
        <select
          value={paintState} // Controlled component with dynamic state
          onChange={(e) => setPaintState(+e.target.value)} 
          className="dropdown"
        >
          <option value="" hidden>Please choose</option>
          <option value="1">By track id</option>
          <option value="2">By STN</option>
        </select>
      </div>
    </div>

<div className="sidebar">
  <button id="toggleButton" onClick={toggleTracksList} >
    {isTracksListVisible ? 'hide tracks list' : 'show tracks list'}
  </button>
  <br></br>
  <div style={{ display: isTracksListVisible ? 'block' : 'none' }}>
  <h3>Tracks List</h3>
  <ul>
    {tracksIDs.length > 0 ? (
      <>
        <li>Past's list:</li>
        {tracksIDs.map((trackId) => (
          <li key={trackId}>
            <button
              id={trackId.toString()}
              name="track"
              onClick={() => handleSeeTrack(trackId)}            
            >
              View Track
            </button>
          </li>
        ))}
      </>
    ) : (
      <li>No tracks from the past, That's what you're here for.</li>
    )}

    <li>--------------</li>
 
    {Object.keys(UiTracks).length > 0 ? (
      <>
        <li>Today's list:</li>
        {Object.keys(UiTracks).map((id) => {
          const trackId = Number(id); // Convert key to number
          return (
            <li key={trackId}>
              {trackId}
              <button
                id={trackId.toString()}
                name="track"
                onClick={() => handleSeeUiTrack(trackId)}
              >
                View Track
              </button>
              <button
                id={trackId.toString()}
                name="track"
                onClick={() => editUiTrack(trackId)}
              >
                edit track
              </button>
            </li>
          );
        })}
      </>
    ) : (
      <li>No tracks created today, don't sleep :)</li>
    )}
  </ul>
</div>
      </div>
    </div>
  );
};

export default Sidebar;
