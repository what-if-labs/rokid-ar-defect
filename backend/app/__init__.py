"""App initialization"""
from .main import app
from .config import get_config
from .models.detection import get_detector
from .services.stream_manager import get_stream_manager

__all__ = ['app', 'get_config', 'get_detector', 'get_stream_manager']
