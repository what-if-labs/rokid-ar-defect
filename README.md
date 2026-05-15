# RTSP Defect Detector

Real-time construction defect detection from RTSP cameras using YOLOv8.

## Features

- 🔴 **Live RTSP Camera Streaming**
- 🤖 **YOLOv8 AI Detection** (15 defect types)
- 🌐 **Web Interface** with real-time overlay
- 📊 **Detection Statistics & History**
- ⚙️ **Configurable via YAML**
- 🐳 **Docker Support**

## Quick Start

### Docker (Recommended)

```bash
# Clone and run
git clone <your-repo>
cd rtsp-defect-detector

# Configure cameras
cp backend/config.example.yaml backend/config.yaml
# Edit config.yaml with your RTSP URLs

# Start
docker-compose up -d

# Access
# Web UI: http://localhost:3000
# API: http://localhost:8000
```

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
uvicorn app.main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

## Configuration

Edit `backend/config.yaml`:

```yaml
cameras:
  - id: "cam_001"
    name: "Site North"
    rtsp_url: "rtsp://admin:password@192.168.1.100:554/stream1"
    enabled: true

detection:
  model_path: "models/yolov8n.pt"
  confidence_threshold: 0.5
  device: "auto"  # cpu, cuda, mps
```

## Defect Classes

| Class | Severity |
|-------|----------|
| crack | major |
| water_damage | major |
| spalling | critical |
| corrosion | critical |
| ... | ... |

## API Endpoints

- `GET /api/cameras` - List cameras
- `GET /api/cameras/{id}/stream` - MJPEG stream
- `GET /api/cameras/{id}/detections` - Latest detections
- `WS /ws/camera/{id}` - WebSocket updates

## License

MIT
