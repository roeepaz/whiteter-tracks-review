import React from "react";

interface HoverInfoProps {
  hoverInfo: {
    longitude: number;
    latitude: number;
    altitude: number;
    t: number;
    is_associate: boolean;
    target_id: number;
    screenX: number;
    screenY: number;
  } | null; // Nullable, as hoverInfo can be null
}

const HoverInfo: React.FC<HoverInfoProps> = ({ hoverInfo }) => {
  if (!hoverInfo) return null; // Do not render if hoverInfo is null

  return (
    <div
      className="hover-info"
      style={{
        left: hoverInfo.screenX + 10,
        top: hoverInfo.screenY + 10,
      }}
    >
      <div>
        <strong>Longitude:</strong> {hoverInfo.longitude.toFixed(2)}
      </div>
      <div>
        <strong>Latitude:</strong> {hoverInfo.latitude.toFixed(2)}
      </div>
      <div>
        <strong>Altitude:</strong> {hoverInfo.altitude.toFixed(2)}
      </div>
      <div>
        <strong>Time:</strong> {hoverInfo.t.toFixed(1)}
      </div>
      <div>
        <strong>target_id:</strong> {hoverInfo.target_id}
      </div>
      <div>
        <strong>Is Associate?</strong> {hoverInfo.is_associate ? "Yes" : "No"}
      </div>
    </div>
  );
};

export default HoverInfo;
