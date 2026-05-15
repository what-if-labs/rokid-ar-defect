import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DetectionOverlay } from '../components/DetectionOverlay';
import { DetectionList } from '../components/DetectionList';
import { useWebSocket } from '../hooks/useWebSocket';
import { useCameraStore } from '../store/cameraStore';
import { Camera, Detection } from '../types';

export function CameraView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { cameras } = useCameraStore();
  const [camera, setCamera] = useState<Camera | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [stats, setStats] = useState({ fps: 0, frameCount: 0, isConnected: false });
  const [showOverlay, setShowOverlay] = useState(true);

  const streamUrl = `http://localhost:8001/api/cameras/${id}/stream`;
  const wsUrl = `ws://localhost:8001/ws/camera/${id}`;
  const { lastMessage, connectionStatus } = useWebSocket(wsUrl);

  useEffect(() => {
    const found = cameras.find((c) => c.id === id);
    if (found) {
      setCamera(found);
    }
  }, [id, cameras]);

  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data);
        setDetections(data.detections);
        setStats({
          fps: data.fps,
          frameCount: data.frame_count,
          isConnected: data.is_connected,
        });
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    }
  }, [lastMessage]);

  if (!camera) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-400">Camera not found</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <button
              onClick={() => navigate('/')}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ← Back
            </button>
            <h1 className="text-xl font-bold text-white">{camera.name}</h1>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span className={`flex items-center gap-1 ${connectionStatus === 'connected' ? 'text-green-400' : 'text-red-400'}`}>
              <span className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-400' : 'bg-red-400'}`} />
              {connectionStatus === 'connected' ? 'Live' : 'Disconnected'}
            </span>
            <span>FPS: {stats.fps.toFixed(1)}</span>
            <span>Frames: {stats.frameCount}</span>
            <span>Detections: {detections.length}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              showOverlay
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
            }`}
          >
            {showOverlay ? 'Hide Overlay' : 'Show Overlay'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Video Stream */}
        <div className="flex-1 relative bg-black">
          <img
            src={streamUrl}
            alt={camera.name}
            className="w-full h-full object-contain"
          />

          {showOverlay && <DetectionOverlay detections={detections} />}

          {connectionStatus !== 'connected' && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80">
              <div className="text-center text-gray-400">
                <div className="text-4xl mb-4">📹</div>
                <p className="text-lg">No Signal</p>
                <p className="text-sm">Waiting for camera...</p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="w-80 bg-gray-800 border-l border-gray-700 overflow-y-auto">
          <DetectionList detections={detections} />
        </div>
      </div>
    </div>
  );
}
