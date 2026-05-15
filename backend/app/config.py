"""RTSP Defect Detector - Configuration Module"""
from pydantic import Field, BaseModel
from typing import List, Optional, Tuple
import yaml
from pathlib import Path


class CameraConfig(BaseModel):
    """Single camera configuration"""
    id: str
    name: str
    rtsp_url: str
    enabled: bool = True
    fps: int = 15
    resolution: Tuple[int, int] = (1280, 720)
    ptz_enabled: bool = False
    ptz_url: Optional[str] = None
    ptz_username: Optional[str] = None
    ptz_password: Optional[str] = None
    source_type: str = "rtsp"  # "rtsp", "webcam", or "test_video"


class DetectionConfig(BaseModel):
    """Detection model configuration"""
    model_path: str = "models/yolov8n.pt"
    confidence_threshold: float = Field(default=0.5, ge=0.1, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.1, le=1.0)
    device: str = "auto"
    input_size: Tuple[int, int] = (640, 640)
    enabled_classes: Optional[List[int]] = None
    max_detections: int = 100
    inference_interval: int = 2


class StreamConfig(BaseModel):
    """Streaming configuration"""
    jpeg_quality: int = Field(default=85, ge=1, le=100)
    stream_fps: int = 15
    buffer_size: int = 10
    reconnect_attempts: int = 3
    reconnect_delay: int = 5


class WebSocketConfig(BaseModel):
    """WebSocket configuration"""
    max_connections: int = 10
    ping_interval: int = 20
    ping_timeout: int = 10


class AppConfig(BaseModel):
    """Main application configuration"""
    app_name: str = "RTSP Defect Detector"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    cameras: List[CameraConfig] = []
    detection: DetectionConfig = DetectionConfig()
    stream: StreamConfig = StreamConfig()
    websocket: WebSocketConfig = WebSocketConfig()
    data_dir: str = "data"
    capture_dir: str = "data/captures"
    log_dir: str = "logs"


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration from YAML file"""
    path = Path(config_path)
    if not path.exists():
        return AppConfig()
    
    with open(path) as f:
        config_dict = yaml.safe_load(f)
    
    return AppConfig(**config_dict)


# Global config
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create global config"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
