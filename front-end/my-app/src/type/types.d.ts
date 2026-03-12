import { Plot } from './types'; 

declare module '@deck.gl/react' {
    const DeckGL: any;
    export default DeckGL;
  }
  
declare module '@deck.gl/core' {
    export const ScatterplotLayer: any;
    export const ArcLayer: any;
    // Add more layers if necessary
  }
// src/declarations.d.ts
declare module './apiServer' {
  export function fetchEvents(): Promise<any>;
  export function fetchEventPlots(eventId: string | number): Promise<Plot[]>;
  export function submitPlots(selectedPlots: Plot[]): Promise<any>;
}

  
  // src/declarations.d.ts
declare module '@deck.gl/layers';
declare module '@deck.gl/core';
declare module '@deck.gl/react';
interface ImportMetaEnv {
  readonly VITE_MAPBOX_TOKEN: string;
  // Add other environment variables here if needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
// src/declarations.d.ts (or any .d.ts file)

interface Window {
  deck?: any;  // Declare deck as a property of window
}
declare module "*.png" {
  const value: string;
  export default value;
}
declare module "*.jpg" {
  const value: string;
  export default value;
}



  