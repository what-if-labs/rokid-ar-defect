import { useState, useEffect } from 'react';
import { CameraCard } from '../components/CameraCard';
import { useCameras } from '../hooks/useCameras';
import { useCameraStore } from '../store/cameraStore';

export function Dashboard() {
  const { cameras, statuses, loading, error, startCamera, stopCamera } = useCameras();
  const { selectCamera } = useCameraStore();
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all');

  const filteredCameras = cameras.filter((cam) => {
    if (filter === 'active') return cam.enabled;
    if (filter === 'inactive') return !cam.enabled;
    return true;
  });

  const getStatus = (cameraId: string) => {
    return statuses.find((s) => s.camera_id === cameraId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading cameras...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-2">Camera Dashboard</h1>
        <p className="text-gray-400">Manage and monitor RTSP cameras</p>
      </div>

      <div className="flex gap-2 mb-6">
        {(['all', 'active', 'inactive'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCameras.map((camera) => (
          <CameraCard
            key={camera.id}
            camera={camera}
            status={getStatus(camera.id)}
            onSelect={() => selectCamera(camera.id)}
            onStart={() => startCamera(camera.id)}
            onStop={() => stopCamera(camera.id)}
          />
        ))}
      </div>

      {filteredCameras.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">No cameras found</p>
          <p className="text-sm">Configure cameras in config.yaml</p>
        </div>
      )}
    </div>
  );
}
