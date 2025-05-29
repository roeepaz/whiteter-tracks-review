import { useRef } from 'react';
import { PickingInfo } from '@deck.gl/core';

type UseDoubleClickProps = {
    pickingInfo : PickingInfo;
  onSingleClick?: (pickingInfo: PickingInfo | undefined, event: React.MouseEvent) => void;
  onDoubleClick?: (pickingInfo: PickingInfo,event: React.MouseEvent) => void;
  delay?: number; // Time to wait for detecting double-clicks (default: 200ms)
};

export const useDoubleClick = ({
pickingInfo,
  onSingleClick,
  onDoubleClick,
  delay = 200,
}: UseDoubleClickProps) => {
  const clickTimeout = useRef<number | null>(null);

  const handleClick = (info: PickingInfo,event: React.MouseEvent) => {
    if (clickTimeout.current) {
      // Clear the timeout if already waiting
      clearTimeout(clickTimeout.current);
      clickTimeout.current = null;

      // Trigger the double-click handler
      if (onDoubleClick) {
        onDoubleClick(info,event);
      }
    } else {
      // Start the timeout for single-click
      clickTimeout.current = window.setTimeout(() => {
        if (onSingleClick) {
          onSingleClick(info,event);
        }
        clickTimeout.current = null;
      }, delay);
    }
  };

  return handleClick;
};
