import { Detection } from '../types';

interface DetectionListProps {
  detections: Detection[];
}

export function DetectionList({ detections }: DetectionListProps) {
  const severityColors = {
    minor: 'bg-yellow-500',
    major: 'bg-orange-500',
    critical: 'bg-red-500',
  };

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold text-white mb-4">Detections</h3>
      
      {detections.length === 0 ? (
        <p className="text-gray-500 text-sm">No defects detected</p>
      ) : (
        <div className="space-y-2">
          {detections.map((det, index) => (
            <div
              key={index}
              className="bg-gray-800 rounded-lg p-3 border border-gray-700"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-white font-medium capitalize">
                  {det.class_name.replace('_', ' ')}
                </span>
                <span className={`text-xs px-2 py-1 rounded text-white ${severityColors[det.severity]}`}>
                  {det.severity}
                </span>
              </div>
              
              <div className="flex items-center justify-between text-sm text-gray-400">
                <span>Confidence: {Math.round(det.confidence * 100)}%</span>
                <span>ID: {det.class_id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
