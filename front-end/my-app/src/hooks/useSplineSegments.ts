import { useMemo, useEffect, useState } from "react";
import {TrackPlot, Segment} from "../type/types";

// generating line segments (spline data) from the tracks for visualization
export const useSplineSegments = (
  tracksToSeeByTime: TrackPlot[],
  viewTrackByTime: TrackPlot[]
) => {
//the line layer need to get segment. this is the Combined segments of the exist tracks and the view track
  const SplineSegments = useMemo(() => {
    const segments: Segment[] = [];
    const tracksGroupedById = tracksToSeeByTime.reduce((acc, plot) => {
      const trackId = plot.id;
      if (!acc[trackId]) {
        acc[trackId] = [];
      }
      acc[trackId].push(plot);
      return acc;
    }, {} as Record<number, TrackPlot[]>);

    Object.values(tracksGroupedById).forEach((splinePoints) => {
      for (let i = 0; i < splinePoints.length - 1; i++) {
        const currentPoint = splinePoints[i];
        const nextPoint = splinePoints[i + 1];
        segments.push({
          source: [
            Number(currentPoint.longitude),
            Number(currentPoint.latitude),
            Number(currentPoint.altitude),
          ],
          target: [
            Number(nextPoint.longitude),
            Number(nextPoint.latitude),
            Number(nextPoint.altitude),
          ],
        });
      }
    });

    return segments;
  }, [tracksToSeeByTime]);

  const SplineSegmentsFotOneTrack = useMemo(() => {
    const segments: Segment[] = [];
    for (let i = 0; i < viewTrackByTime.length - 1; i++) {
      const currentPoint = viewTrackByTime[i];
      const nextPoint = viewTrackByTime[i + 1];
      segments.push({
        source: [
          Number(currentPoint.longitude),
          Number(currentPoint.latitude),
          Number(currentPoint.altitude),
        ],
        target: [
          Number(nextPoint.longitude),
          Number(nextPoint.latitude),
          Number(nextPoint.altitude),
        ],
      });
    }
    return segments;
  }, [viewTrackByTime]);

  const [combinedSplineData, setCombinedSplineData] = useState<Segment[]>([]);

  useEffect(() => {
    setCombinedSplineData([...SplineSegments, ...SplineSegmentsFotOneTrack]);
  }, [SplineSegments, SplineSegmentsFotOneTrack]);

  return { combinedSplineData};
};
