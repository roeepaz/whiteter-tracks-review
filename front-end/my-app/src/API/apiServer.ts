// src/api/api.ts
import { Plot, TrackData, DictData, BackendResponse } from '../type/types';
import { parseErrorFromResponse } from '../utils/apiErrorHandler';
import { markPerf, resetMetrics, PERF_MODE } from '../utils/perfUtils';

const BASE_URL = 'https://127.0.0.1:5000';

/**
 * desc
 * @date 2025-04-16
 * @returns { Promise<string[]> }
 */
export const fetchEvents = async (): Promise<string[]> => {
  const response = await fetch(`${BASE_URL}/api/events`);
  if (!response.ok) throw await parseErrorFromResponse(response);

  const data = await response.json();
  if (!data.success || !Array.isArray(data.data)) throw new Error("Invalid data format");
  return data.data.map((event: string) => event.trim());
};

/**
 * desc
 * @date 2025-04-16
 * @param { string | number | undefined } eventId
 * @returns { Promise<DictData> }
 */
export const fetchEventPlots = async (eventId: string | number | undefined): Promise<DictData> => {
  // Reset metrics for each new event load
  if (PERF_MODE) resetMetrics();
  markPerf('T1_FETCH_START', { eventId });

  const response = await fetch(`${BASE_URL}/api/get-event/${eventId}`);
  if (!response.ok) throw await parseErrorFromResponse(response);

  markPerf('T2_RESPONSE_RECEIVED', {
    status: response.status,
    contentLength: response.headers.get('content-length'),
    backendLoadMs: response.headers.get('X-Backend-Load-Time-Ms'),
    backendSerializeMs: response.headers.get('X-Backend-Serialize-Time-Ms'),
  });

  const data = await response.json();
  markPerf('T3_JSON_PARSED');

  console.log(data)
  if (!data.success || !data.data) throw new Error("Invalid event plot data format");
  return data.data;
};

/**
 * desc
 * @date 2025-04-16
 * @param { { selectedPlots: Plot[]; smoothingFactor: number } } parm1
 * @returns { Promise<any> }
 */
export const submitPlots = async ({ selectedPlots, smoothingFactor }: { selectedPlots: Plot[]; smoothingFactor: number }): Promise<any> => {
  const response = await fetch(`${BASE_URL}/creat-track`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: selectedPlots, smoothingFactor })
  });
  if (!response.ok) throw await parseErrorFromResponse(response);

  const data = await response.json();
  if (!data.success || !data.data) throw new Error("Failed to create track");
  return data.data;
};

/**
 * desc
 * @date 2025-04-16
 * @param { { selectedPlots: Plot[], eventId: string | undefined, recommendationType: string } } parm1
 * @returns { Promise<any> }
 */
export const getRecommendation = async ({ selectedPlots, eventId, recommendationType }: { selectedPlots: Plot[], eventId: string | undefined, recommendationType: string }): Promise<any> => {
  const response = await fetch(`${BASE_URL}/get-recommendation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plots: selectedPlots, eventId, recommendationType })
  });
  if (!response.ok) throw await parseErrorFromResponse(response);

  const data = await response.json();
  if (!data.success || !data.data) throw new Error("Invalid recommendation response");
  return data.data;
};

/**
 * desc
 * @date 2025-04-16
 * @param { string | undefined } event_id
 * @param { Record<number, TrackData> } tracks
 * @param { number[] } notes
 * @returns { Promise<BackendResponse> }
 */
export const sentEventTracks = async (event_id: string | undefined, tracks: Record<number, TrackData>, notes: number[]): Promise<BackendResponse> => {
  const response = await fetch(`${BASE_URL}/submit-event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_id, tracks, notes })
  });
  if (!response.ok) throw await parseErrorFromResponse(response);

  const data = await response.json();
  if (!data.success) throw new Error("Event submission failed");
  return data;
};

/**
 * desc
 * @date 2025-04-16
 * @returns { Promise<any> }
 */
export const fetchConfig = async (): Promise<any> => {
  const response = await fetch(`${BASE_URL}/config`);
  if (!response.ok) throw await parseErrorFromResponse(response);

  const data = await response.json();
  if (!data.success || !data.data) throw new Error("Failed to load config");
  return data.data;
};
