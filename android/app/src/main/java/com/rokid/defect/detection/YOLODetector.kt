package com.rokid.defect.detection

import android.content.Context
import android.graphics.Bitmap
import android.graphics.RectF
import android.util.Log
import ai.onnxruntime.*
import java.nio.FloatBuffer

data class Detection(
    val classId: Int,
    val className: String,
    val confidence: Float,
    val boundingBox: RectF
)

class YOLODetector(context: Context) {
    
    companion object {
        private const val TAG = "YOLODetector"
        private const val INPUT_SIZE = 640
        private const val CONFIDENCE_THRESHOLD = 0.5f
        private val CLASS_NAMES = arrayOf(
            "crack", "water_damage", "surface_defect", "missing_element", "alignment_issue",
            "color_defect", "spalling", "corrosion", "efflorescence", "joint_failure",
            "peeling_paint", "rust_stain", "mold_growth", "structural_damage", "loose_fastener"
        )
    }

    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val session: OrtSession

    init {
        val modelPath = "models/yolo26n.onnx"
        val inputStream = context.assets.open(modelPath)
        val modelBytes = inputStream.readBytes()
        inputStream.close()

        val sessionOptions = OrtSession.SessionOptions()
        session = env.createSession(modelBytes, sessionOptions)
        Log.d(TAG, "YOLO model loaded successfully")
    }

    fun detect(bitmap: Bitmap): List<Detection> {
        // Resize to input size
        val resized = Bitmap.createScaledBitmap(bitmap, INPUT_SIZE, INPUT_SIZE, true)
        
        // Convert to float array [1, 3, 640, 640]
        val inputArray = bitmapToFloatArray(resized)
        
        // Create tensor
        val shape = longArrayOf(1, 3, INPUT_SIZE.toLong(), INPUT_SIZE.toLong())
        val tensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(inputArray), shape)
        
        // Run inference
        val results = session.run(mapOf("images" to tensor))
        val output = results.get(0).value as Array<FloatArray>
        
        // Parse detections
        val detections = parseDetections(output[0], bitmap.width, bitmap.height)
        
        // Cleanup
        tensor.close()
        results.close()
        resized.recycle()
        
        return detections
    }

    private fun bitmapToFloatArray(bitmap: Bitmap): FloatArray {
        val width = bitmap.width
        val height = bitmap.height
        val pixels = IntArray(width * height)
        bitmap.getPixels(pixels, 0, width, 0, 0, width, height)
        
        val floatArray = FloatArray(3 * width * height)
        
        // Convert to CHW format and normalize to [0, 1]
        for (i in pixels.indices) {
            val pixel = pixels[i]
            val r = ((pixel shr 16) and 0xFF).toFloat()
            val g = ((pixel shr 8) and 0xFF).toFloat()
            val b = (pixel and 0xFF).toFloat()
            floatArray[i] = r / 255.0f
            floatArray[width * height + i] = g / 255.0f
            floatArray[2 * width * height + i] = b / 255.0f
        }
        
        return floatArray
    }

    private fun parseDetections(output: FloatArray, origWidth: Int, origHeight: Int): List<Detection> {
        val detections = mutableListOf<Detection>()
        
        // Output shape: [1, 300, 6] -> [batch, num_detections, 6]
        // Each detection: [x_center, y_center, width, height, confidence, class_id]
        val numDetections = 300
        val numClasses = CLASS_NAMES.size
        
        for (i in 0 until numDetections) {
            val offset = i * (4 + 1 + numClasses)
            val xCenter = output[offset]
            val yCenter = output[offset + 1]
            val width = output[offset + 2]
            val height = output[offset + 3]
            val confidence = output[offset + 4]
            
            if (confidence > CONFIDENCE_THRESHOLD) {
                // Find best class
                var bestClassId = 0
                var bestClassScore = 0f
                for (c in 0 until numClasses) {
                    val score = output[offset + 5 + c]
                    if (score > bestClassScore) {
                        bestClassScore = score
                        bestClassId = c
                    }
                }
                
                // Convert to original image coordinates
                val scale = INPUT_SIZE.toFloat()
                val ow = origWidth.toFloat()
                val oh = origHeight.toFloat()
                val x1 = ((xCenter - width / 2f) * ow / scale).coerceIn(0f, ow)
                val y1 = ((yCenter - height / 2f) * oh / scale).coerceIn(0f, oh)
                val x2 = ((xCenter + width / 2f) * ow / scale).coerceIn(0f, ow)
                val y2 = ((yCenter + height / 2f) * oh / scale).coerceIn(0f, oh)
                
                detections.add(Detection(
                    classId = bestClassId,
                    className = CLASS_NAMES.getOrElse(bestClassId) { "unknown" },
                    confidence = confidence,
                    boundingBox = RectF(x1, y1, x2, y2)
                ))
            }
        }
        
        return detections
    }

    fun close() {
        session.close()
        env.close()
    }
}
