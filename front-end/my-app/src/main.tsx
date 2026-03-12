import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './pages/App';
import './styles/index.css';

const container = document.getElementById('root');

// Check if the container exists before creating the root
if (container) {
  createRoot(container).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
} else {
  console.error("Root container not found. Unable to mount the app.");
}
