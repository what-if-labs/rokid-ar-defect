export interface Camera {
  id: string;
  name: string;
  enabled: boolean;
  resolution: [number, number];
  fps: number;
  rtsp_url?: string;
}

export interface Detection {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
  severity: 'minor' | 'major' | 'critical';
}

export interface CameraStatus {
  camera_id: string;
  name: string;
  is_running: boolean;
  is_connected: boolean;
  fps: number;
  frame_count: number;
}

export interface WebSocketMessage {
  camera_id: string;
  timestamp: string;
  is_connected: boolean;
  fps: number;
  frame_count: number;
  detections: Detection[];
}
