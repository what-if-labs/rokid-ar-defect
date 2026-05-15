import { useEffect, useState } from 'react';
import axios from 'axios';
import { Camera, CameraStatus } from '../types';

const API_URL = 'http://localhost:8001';

export function useCameras() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [statuses, setStatuses] = useState<CameraStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCameras = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/cameras`);
      setCameras(response.data.cameras);
      setStatuses(response.data.status);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch cameras');
      setLoading(false);
    }
  };

  const startCamera = async (cameraId: string) => {
    try {
      await axios.post(`${API_URL}/api/cameras/${cameraId}/start`);
      await fetchCameras();
    } catch (err) {
      console.error('Failed to start camera:', err);
    }
  };

  const stopCamera = async (cameraId: string) => {
    try {
      await axios.post(`${API_URL}/api/cameras/${cameraId}/stop`);
      await fetchCameras();
    } catch (err) {
      console.error('Failed to stop camera:', err);
    }
  };

  useEffect(() => {
    fetchCameras();
    const interval = setInterval(fetchCameras, 5000);
    return () => clearInterval(interval);
  }, []);

  return { cameras, statuses, loading, error, startCamera, stopCamera, refetch: fetchCameras };
}
