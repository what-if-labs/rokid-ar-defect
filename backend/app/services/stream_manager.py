"""Stream Manager Service"""
import logging
from typing import Dict, List, Optional
from threading import Lock

from ..config import get_config
from ..models.rtsp_stream import RTSPStream, Frame
from ..models.detection import get_detector, DetectionResult

logger = logging.getLogger(__name__)


class StreamManager:
    """Manages multiple RTSP streams"""
    
    def __init__(self):
        self.config = get_config()
        self.streams: Dict[str, RTSPStream] = {}
        self._lock = Lock()
        
        self.latest_detections: Dict[str, List[DetectionResult]] = {}
        self.latest_frames: Dict[str, Frame] = {}
        
        self._init_streams()
    
    def _init_streams(self):
        """Initialize streams from configuration"""
        for cam_config in self.config.cameras:
            if cam_config.enabled:
                self.add_stream(cam_config)
    
    def add_stream(self, cam_config) -> RTSPStream:
        """Add a new stream"""
        stream = RTSPStream(
            camera_config=cam_config,
            stream_config=self.config.stream,
            frame_callback=lambda f, cid=cam_config.id: self._on_frame(f, cid),
        )
        
        with self._lock:
            self.streams[cam_config.id] = stream
        
        return stream
    
    def remove_stream(self, camera_id: str):
        """Remove a stream"""
        with self._lock:
            if camera_id in self.streams:
                self.streams[camera_id].stop()
                del self.streams[camera_id]
                
                if camera_id in self.latest_detections:
                    del self.latest_detections[camera_id]
                if camera_id in self.latest_frames:
                    del self.latest_frames[camera_id]
    
    def start_stream(self, camera_id: str) -> bool:
        """Start a specific stream"""
        with self._lock:
            if camera_id in self.streams:
                return self.streams[camera_id].start()
        return False
    
    def stop_stream(self, camera_id: str):
        """Stop a specific stream"""
        with self._lock:
            if camera_id in self.streams:
                self.streams[camera_id].stop()
    
    def start_all(self):
        """Start all streams"""
        with self._lock:
            for stream in self.streams.values():
                stream.start()
    
    def stop_all(self):
        """Stop all streams"""
        with self._lock:
            for stream in self.streams.values():
                stream.stop()
    
    def _on_frame(self, frame: Frame, camera_id: str):
        """Handle new frame from stream"""
        self.latest_frames[camera_id] = frame
        
        if frame.frame_number % self.config.detection.inference_interval == 0:
            self._run_detection(frame, camera_id)
    
    def _run_detection(self, frame: Frame, camera_id: str):
        """Run detection on frame"""
        try:
            detector = get_detector()
            detections, annotated = detector.detect(frame.image)
            
            self.latest_detections[camera_id] = detections
            
            if annotated is not None:
                self.latest_frames[camera_id] = Frame(
                    image=annotated,
                    timestamp=frame.timestamp,
                    frame_number=frame.frame_number,
                )
                
        except Exception as e:
            logger.error(f"Detection error: {e}")
    
    def get_stream(self, camera_id: str) -> Optional[RTSPStream]:
        """Get stream by ID"""
        with self._lock:
            return self.streams.get(camera_id)
    
    def get_all_streams(self) -> List[RTSPStream]:
        """Get all streams"""
        with self._lock:
            return list(self.streams.values())
    
    def get_status(self) -> List[dict]:
        """Get status of all streams"""
        with self._lock:
            return [s.get_status() for s in self.streams.values()]


# Global manager
_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """Get or create global stream manager"""
    global _manager
    if _manager is None:
        _manager = StreamManager()
    return _manager
