"""FastAPI Main Application"""
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from datetime import datetime

from .config import get_config
from .models.detection import get_detector
from .services.stream_manager import get_stream_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting up...")
    
    detector = get_detector()
    if not detector.initialize():
        logger.error("Failed to initialize detector")
    
    manager = get_stream_manager()
    manager.start_all()
    
    yield
    
    logger.info("Shutting down...")
    manager.stop_all()


config = get_config()
app = FastAPI(
    title="RTSP Defect Detector",
    description="Web-based RTSP camera defect detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": config.app_name,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/api/cameras")
async def list_cameras():
    """List all configured cameras"""
    manager = get_stream_manager()
    return {
        "cameras": [
            {
                "id": cam.id,
                "name": cam.name,
                "enabled": cam.enabled,
                "resolution": cam.resolution,
                "fps": cam.fps,
            }
            for cam in config.cameras
        ],
        "status": manager.get_status(),
    }


@app.post("/api/cameras/{camera_id}/start")
async def start_camera(camera_id: str):
    """Start a camera stream"""
    manager = get_stream_manager()
    success = manager.start_stream(camera_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start camera")
    
    return {"status": "started", "camera_id": camera_id}


@app.post("/api/cameras/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """Stop a camera stream"""
    manager = get_stream_manager()
    manager.stop_stream(camera_id)
    return {"status": "stopped", "camera_id": camera_id}


@app.get("/api/cameras/{camera_id}/stream")
async def camera_stream(camera_id: str, quality: int = 85):
    """MJPEG stream endpoint"""
    manager = get_stream_manager()
    
    async def generate():
        while True:
            frame_data = manager.latest_frames.get(camera_id)
            
            if frame_data is None:
                await asyncio.sleep(0.1)
                continue
            
            ret, buffer = cv2.imencode('.jpg', frame_data.image, [
                cv2.IMWRITE_JPEG_QUALITY, quality
            ])
            
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            
            await asyncio.sleep(1.0 / config.stream.stream_fps)
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/cameras/{camera_id}/detections")
async def get_detections(camera_id: str):
    """Get latest detections for a camera"""
    manager = get_stream_manager()
    detections = manager.latest_detections.get(camera_id, [])
    
    return {
        "camera_id": camera_id,
        "timestamp": datetime.now().isoformat(),
        "count": len(detections),
        "detections": [d.to_dict() for d in detections],
    }


@app.get("/api/model/info")
async def model_info():
    """Get detection model information"""
    detector = get_detector()
    return detector.get_model_info()


@app.websocket("/ws/camera/{camera_id}")
async def websocket_camera(websocket: WebSocket, camera_id: str):
    """WebSocket for real-time detection updates"""
    await websocket.accept()
    
    manager = get_stream_manager()
    
    try:
        while True:
            detections = manager.latest_detections.get(camera_id, [])
            frame_data = manager.latest_frames.get(camera_id)
            stream = manager.get_stream(camera_id)
            
            data = {
                "camera_id": camera_id,
                "timestamp": datetime.now().isoformat(),
                "is_connected": stream.is_connected if stream else False,
                "fps": round(stream.fps, 2) if stream else 0,
                "frame_count": stream.frame_count if stream else 0,
                "detections": [d.to_dict() for d in detections],
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
