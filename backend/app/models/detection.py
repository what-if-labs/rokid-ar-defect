"""YOLO Defect Detection Model"""
import cv2
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from ultralytics import YOLO
import logging

from ..config import get_config

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Single detection result"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    severity: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 3),
            "bbox": self.bbox,
            "severity": self.severity,
        }


class YOLODefectDetector:
    """YOLOv8-based construction defect detector"""
    
    DEFECT_CLASSES = {
        0: "crack",
        1: "water_damage",
        2: "surface_defect",
        3: "missing_element",
        4: "alignment_issue",
        5: "color_defect",
        6: "spalling",
        7: "corrosion",
        8: "efflorescence",
        9: "joint_failure",
        10: "peeling_paint",
        11: "rust_stain",
        12: "mold_growth",
        13: "structural_damage",
        14: "loose_fastener",
    }
    
    SEVERITY_MAP = {
        "crack": "major",
        "water_damage": "major",
        "surface_defect": "minor",
        "missing_element": "major",
        "alignment_issue": "major",
        "color_defect": "minor",
        "spalling": "critical",
        "corrosion": "critical",
        "efflorescence": "minor",
        "joint_failure": "critical",
        "peeling_paint": "minor",
        "rust_stain": "major",
        "mold_growth": "critical",
        "structural_damage": "critical",
        "loose_fastener": "major",
    }
    
    def __init__(self):
        self.config = get_config().detection
        self.model = None
        self.device = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize the detector"""
        try:
            logger.info("Initializing YOLO detector...")
            
            # Determine device
            if self.config.device == "auto":
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"
            else:
                self.device = self.config.device
            
            logger.info(f"Using device: {self.device}")
            
            # Load model
            model_path = Path(self.config.model_path)
            if not model_path.exists():
                logger.warning(f"Model not found at {model_path}, downloading YOLOv8n...")
                self.model = YOLO("yolov8n.pt")
                model_path.parent.mkdir(parents=True, exist_ok=True)
                self.model.save(str(model_path))
            else:
                self.model = YOLO(str(model_path))
            
            self.model.to(self.device)
            
            # Warm up
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(dummy, verbose=False)
            
            self._initialized = True
            logger.info("YOLO detector initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize detector: {e}")
            return False
    
    def detect(self, image: np.ndarray, draw_boxes: bool = True) -> Tuple[List[DetectionResult], Optional[np.ndarray]]:
        """Run detection on image"""
        if not self._initialized:
            logger.error("Detector not initialized")
            return [], None
        
        try:
            results = self.model.predict(
                image,
                conf=self.config.confidence_threshold,
                iou=self.config.iou_threshold,
                verbose=False,
                device=self.device,
                imgsz=self.config.input_size,
                max_det=self.config.max_detections,
            )
            
            detections = []
            result = results[0]
            
            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if self.config.enabled_classes is not None:
                        if cls_id not in self.config.enabled_classes:
                            continue
                    
                    class_name = self.DEFECT_CLASSES.get(cls_id, f"class_{cls_id}")
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    severity = self.SEVERITY_MAP.get(class_name, "minor")
                    
                    detections.append(DetectionResult(
                        class_id=cls_id,
                        class_name=class_name,
                        confidence=confidence,
                        bbox=(x1, y1, x2, y2),
                        severity=severity,
                    ))
            
            annotated_image = None
            if draw_boxes:
                annotated_image = self._draw_detections(image.copy(), detections)
            
            return detections, annotated_image
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return [], None
    
    def _draw_detections(self, image: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """Draw detection boxes on image"""
        for det in detections:
            color_map = {
                "minor": (0, 255, 255),
                "major": (0, 140, 255),
                "critical": (0, 0, 255),
            }
            color = color_map.get(det.severity, (0, 255, 0))
            x1, y1, x2, y2 = det.bbox
            
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            label = f"{det.class_name}: {det.confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            cv2.rectangle(
                image,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1,
            )
            
            cv2.putText(
                image,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2,
            )
            
            severity_label = det.severity.upper()
            cv2.putText(
                image,
                severity_label,
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )
        
        return image
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_path": self.config.model_path,
            "device": self.device,
            "input_size": self.config.input_size,
            "confidence_threshold": self.config.confidence_threshold,
            "num_classes": len(self.DEFECT_CLASSES),
            "classes": self.DEFECT_CLASSES,
            "initialized": self._initialized,
        }


# Global detector
_detector: Optional[YOLODefectDetector] = None


def get_detector() -> YOLODefectDetector:
    """Get or create global detector"""
    global _detector
    if _detector is None:
        _detector = YOLODefectDetector()
        _detector.initialize()
    return _detector
