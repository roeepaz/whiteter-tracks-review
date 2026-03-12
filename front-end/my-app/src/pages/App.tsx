import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from "./Login";
import EventsPage from "./EventsPage";
import Map from "./Map";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
const queryClient = new QueryClient();
import '../styles/base.css';
import '../styles/layout.css';
import '../styles/utilities.css'
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<Login />} />
           <Route path="/Map/:eventId" element={<Map />} />  
          <Route path="/event-page" element={<EventsPage />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
