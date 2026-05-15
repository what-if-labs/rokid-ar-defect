import { Detection } from '../types';

interface DetectionOverlayProps {
  detections: Detection[];
}

export function DetectionOverlay({ detections }: DetectionOverlayProps) {
  const severityColors = {
    minor: '#FCD34D',
    major: '#FB923C',
    critical: '#EF4444',
  };

  return (
    <div className="absolute inset-0 pointer-events-none">
      {detections.map((det, index) => {
        const [x1, y1, x2, y2] = det.bbox;
        const color = severityColors[det.severity];

        const left = (x1 / 1920) * 100;
        const top = (y1 / 1080) * 100;
        const width = ((x2 - x1) / 1920) * 100;
        const height = ((y2 - y1) / 1080) * 100;

        return (
          <div
            key={`${det.class_name}-${index}`}
            className="absolute border-2"
            style={{
              left: `${left}%`,
              top: `${top}%`,
              width: `${width}%`,
              height: `${height}%`,
              borderColor: color,
              boxShadow: `0 0 10px ${color}40`,
            }}
          >
            <div
              className="absolute -top-6 left-0 px-2 py-0.5 text-xs font-bold text-white rounded"
              style={{ backgroundColor: color }}
            >
              {det.class_name.replace('_', ' ')} {Math.round(det.confidence * 100)}%
            </div>

            <div
              className="absolute -bottom-5 left-0 px-2 py-0.5 text-xs font-bold rounded"
              style={{
                backgroundColor: `${color}40`,
                color: color,
                border: `1px solid ${color}`,
              }}
            >
              {det.severity.toUpperCase()}
            </div>
          </div>
        );
      })}
    </div>
  );
}
