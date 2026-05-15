import { Camera, CameraStatus } from '../types';

interface CameraCardProps {
  camera: Camera;
  status?: CameraStatus;
  onSelect: () => void;
  onStart: () => void;
  onStop: () => void;
}

export function CameraCard({ camera, status, onSelect, onStart, onStop }: CameraCardProps) {
  const isConnected = status?.is_connected ?? false;
  const isRunning = status?.is_running ?? false;

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-white">{camera.name}</h3>
          <p className="text-sm text-gray-400">{camera.id}</p>
        </div>
        
        <div className={`flex items-center gap-1 text-sm ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4 text-sm text-gray-400">
        <div>Resolution: {camera.resolution[0]}x{camera.resolution[1]}</div>
        <div>FPS: {camera.fps}</div>
        {status && (
          <>
            <div>Current FPS: {status.fps.toFixed(1)}</div>
            <div>Frames: {status.frame_count}</div>
          </>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={onSelect}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
        >
          View
        </button>
        
        {isRunning ? (
          <button
            onClick={onStop}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Stop
          </button>
        ) : (
          <button
            onClick={onStart}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Start
          </button>
        )}
      </div>
    </div>
  );
}
