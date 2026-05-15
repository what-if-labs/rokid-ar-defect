"""RTSP Stream Handler"""
import cv2
import numpy as np
import threading
import time
import logging
from typing import Optional, Callable
from dataclasses import dataclass
from queue import Queue, Full

from ..config import CameraConfig, StreamConfig

logger = logging.getLogger(__name__)


@dataclass
class Frame:
    """Video frame container"""
    image: np.ndarray
    timestamp: float
    frame_number: int


class RTSPStream:
    """RTSP video stream handler"""
    
    def __init__(
        self,
        camera_config: CameraConfig,
        stream_config: StreamConfig,
        frame_callback: Optional[Callable[[Frame], None]] = None,
    ):
        self.camera_config = camera_config
        self.stream_config = stream_config
        self.frame_callback = frame_callback
        
        self.url = camera_config.rtsp_url
        self.name = camera_config.name
        self.camera_id = camera_config.id
        
        self.is_running = False
        self.is_connected = False
        self.frame_count = 0
        self.fps = 0.0
        self.last_frame_time = 0.0
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.frame_buffer: Queue[Frame] = Queue(maxsize=stream_config.buffer_size)
        self._cap: Optional[cv2.VideoCapture] = None
        self._reconnect_attempts = 0
        
    def start(self) -> bool:
        """Start the stream"""
        if self.is_running:
            logger.warning(f"Stream {self.camera_id} already running")
            return True
        
        logger.info(f"Starting stream: {self.name} ({self.url})")
        
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
        
        return True
    
    def stop(self):
        """Stop the stream"""
        logger.info(f"Stopping stream: {self.name}")
        self.is_running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        if self._cap:
            self._cap.release()
            self._cap = None
        
        self.is_connected = False
    
    def _generate_test_frame(self) -> np.ndarray:
        """Generate a synthetic test frame with moving shapes"""
        w, h = self.camera_config.resolution
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (30, 30, 40)  # Dark background
        
        self._test_video_frame += 1
        t = self._test_video_frame
        
        # Moving rectangles (simulating objects to detect)
        cv2.rectangle(frame,
            (50 + (t * 3) % (w - 150), 50 + (t * 2) % (h - 150)),
            (200 + (t * 3) % (w - 150), 200 + (t * 2) % (h - 150)),
            (100, 100, 200), -1)
        
        # Static "crack" line
        cv2.line(frame, (w // 3, h // 4), (w // 2, 3 * h // 4), (200, 200, 100), 3)
        
        # Timestamp overlay
        cv2.putText(frame, f"TEST FRAME {t}", (10, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame

    def _stream_loop(self):
        """Main streaming loop"""
        while self.is_running and not self._stop_event.is_set():
            try:
                if not self.is_connected:
                    if not self._connect():
                        time.sleep(self.stream_config.reconnect_delay)
                        continue
                
                # Test video mode: generate synthetic frames
                if self.camera_config.source_type == "test_video":
                    frame = self._generate_test_frame()
                    self.frame_count += 1
                    current_time = time.time()
                    
                    if self.last_frame_time > 0:
                        self.fps = 1.0 / (current_time - self.last_frame_time)
                    self.last_frame_time = current_time
                    
                    frame_obj = Frame(
                        image=frame,
                        timestamp=current_time,
                        frame_number=self.frame_count,
                    )
                    
                    try:
                        self.frame_buffer.put_nowait(frame_obj)
                    except Full:
                        try:
                            self.frame_buffer.get_nowait()
                            self.frame_buffer.put_nowait(frame_obj)
                        except:
                            pass
                    
                    if self.frame_callback:
                        try:
                            self.frame_callback(frame_obj)
                        except Exception as e:
                            logger.error(f"Frame callback error: {e}")
                    
                    time.sleep(1.0 / self.camera_config.fps)
                    continue
                
                # RTSP/Webcam mode: read from capture
                ret, frame = self._cap.read()
                
                if not ret:
                    logger.warning(f"Failed to read frame from {self.name}")
                    self._handle_disconnect()
                    continue
                
                self.frame_count += 1
                current_time = time.time()
                
                if self.last_frame_time > 0:
                    self.fps = 1.0 / (current_time - self.last_frame_time)
                
                self.last_frame_time = current_time
                
                frame_obj = Frame(
                    image=frame,
                    timestamp=current_time,
                    frame_number=self.frame_count,
                )
                
                try:
                    self.frame_buffer.put_nowait(frame_obj)
                except Full:
                    try:
                        self.frame_buffer.get_nowait()
                        self.frame_buffer.put_nowait(frame_obj)
                    except:
                        pass
                
                if self.frame_callback:
                    try:
                        self.frame_callback(frame_obj)
                    except Exception as e:
                        logger.error(f"Frame callback error: {e}")
                
                time.sleep(1.0 / self.camera_config.fps)
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                self._handle_disconnect()
                time.sleep(self.stream_config.reconnect_delay)
    
    def _connect(self) -> bool:
        """Connect to RTSP stream, webcam, or generate test video"""
        try:
            logger.info(f"Connecting to {self.name}...")
            
            # Test video mode: generate synthetic frames
            if self.camera_config.source_type == "test_video":
                self._test_video_frame = 0
                self.is_connected = True
                self._reconnect_attempts = 0
                logger.info(f"Test video mode enabled for {self.name}")
                return True
            
            # Webcam mode: use camera index (0 = default webcam)
            if self.camera_config.source_type == "webcam":
                camera_index = int(self.url) if self.url.isdigit() else 0
                logger.info(f"Opening webcam index {camera_index}")
                self._cap = cv2.VideoCapture(camera_index)
            else:
                self._cap = cv2.VideoCapture(self.url)
            
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._cap.set(cv2.CAP_PROP_FPS, self.camera_config.fps)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config.resolution[0])
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config.resolution[1])
            
            ret, _ = self._cap.read()
            if not ret:
                source = self.camera_config.source_type if self.camera_config.source_type != "rtsp" else "RTSP"
                raise Exception(f"Failed to read test frame from {source}")
            
            self.is_connected = True
            self._reconnect_attempts = 0
            logger.info(f"Connected to {self.name}")
            
            return True
            
        except Exception as e:
            self._reconnect_attempts += 1
            logger.error(f"Connection failed (attempt {self._reconnect_attempts}): {e}")
            
            if self._cap:
                self._cap.release()
                self._cap = None
            
            if self._reconnect_attempts >= self.stream_config.reconnect_attempts:
                logger.error(f"Max reconnection attempts reached for {self.name}")
                self.is_running = False
            
            return False
    
    def _handle_disconnect(self):
        """Handle disconnection"""
        self.is_connected = False
        if self._cap:
            self._cap.release()
            self._cap = None
    
    def get_frame(self, timeout: float = 1.0) -> Optional[Frame]:
        """Get latest frame from buffer"""
        try:
            return self.frame_buffer.get(timeout=timeout)
        except:
            return None
    
    def get_status(self) -> dict:
        """Get stream status"""
        return {
            "camera_id": self.camera_id,
            "name": self.name,
            "is_running": self.is_running,
            "is_connected": self.is_connected,
            "fps": round(self.fps, 2),
            "frame_count": self.frame_count,
            "url": self.url,
            "resolution": self.camera_config.resolution,
        }
