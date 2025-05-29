import React, { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchEvents } from '../API/apiServer';
import '../styles/eventsPage.css';
import axios, { AxiosError } from 'axios';
import '../styles/errorsAndLoader.css';

const EventsPage = () => {
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [filteredEvents, setFilteredEvents] = useState<string[]>([]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Fetch events data using React Query
  const {
    data: events = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<string[], Error>({
    queryKey: ['events'],
    queryFn: fetchEvents,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim();
    setQuery(value);

    if (!value || !Array.isArray(events)) {
      setFilteredEvents([]);
      return;
    }

    const matches = events.filter(event => {
      const normalizedEvent = event.toLowerCase().replace(/\s/g, '');
      const normalizedValue = value.toLowerCase().replace(/\s/g, '');
      return normalizedEvent.includes(normalizedValue);
    });

    setFilteredEvents(matches);
  };

  const handleEventSelection = (event: string) => {
    navigate(`/Map/${event}`);
  };

  if (isLoading) {
    return (
      <div className="full-page-loader">
        <div className="spinner"></div>
        <h1>Loading events...</h1>
      </div>
    );
  }

  if (isError && error instanceof Error) {
    const match = error.message.match(/^\[(.*?)\]\s(.*)/);
    const errorType = match?.[1] || 'Error';
    const errorMessage = match?.[2] || error.message;

    return (
      <div className="error-container">
        <div className="evets_error-img"></div>
        <p><strong>{errorType}</strong></p>
        <p>{errorMessage}</p>
        <button onClick={() => refetch()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="image">
        <div className="image-overlay">
          <div className="center-box">
            <div className="image-text">
              Please enter a name or part of an event name to open it
            </div>

            <div className="search-container">
              <input
                ref={inputRef}
                type="text"
                placeholder="Search event..."
                value={query}
                onChange={handleInputChange}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && filteredEvents.length > 0) {
                    handleEventSelection(filteredEvents[0]);
                  }
                }}
                className="search-input"
              />
              {filteredEvents.length > 0 && (
                <ul className="search-results">
                  {filteredEvents.map((event, index) => (
                    <li
                      key={index}
                      className="search-item"
                      onClick={() => handleEventSelection(event)}
                      onMouseEnter={() => setQuery(event)} // 👈 Hover sets input text
                    >
                      <span>{event}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventsPage;
