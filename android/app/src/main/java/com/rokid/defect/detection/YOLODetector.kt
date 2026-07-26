package com.rokid.defect.detection

import android.content.Context
import android.graphics.Bitmap
import android.graphics.RectF
import android.util.Log
import ai.onnxruntime.*
import java.nio.FloatBuffer

data class Detection(
    val className: String,
    val confidence: Float,
    val boundingBox: RectF
)

class YOLODetector(context: Context) {

    companion object {
        private const val TAG = "YOLODetector"
        private const val INPUT_SIZE = 640
        private const val CONFIDENCE_THRESHOLD = 0.4f
        private const val CLASS_NAME = "person"
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
        Log.d(TAG, "YOLO people detection model loaded")
    }

    fun detect(bitmap: Bitmap): List<Detection> {
        val resized = Bitmap.createScaledBitmap(bitmap, INPUT_SIZE, INPUT_SIZE, true)

        // Convert to float array [1, 3, 640, 640]
        val inputArray = bitmapToFloatArray(resized)

        // Create input tensor
        val shape = longArrayOf(1, 3, INPUT_SIZE.toLong(), INPUT_SIZE.toLong())
        val tensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(inputArray), shape)

        // Run inference
        val results = session.run(mapOf("images" to tensor))

        // Output shape: [1, 300, 6] -> Array<Array<FloatArray>>
        @Suppress("UNCHECKED_CAST")
        val output = results.get(0).value as Array<Array<FloatArray>>

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

    private fun parseDetections(output: Array<FloatArray>, origWidth: Int, origHeight: Int): List<Detection> {
        val detections = mutableListOf<Detection>()

        // Output: 300 detections, each [x_center, y_center, width, height, confidence, class_id]
        // Coordinates are in [0, 640] range (input size)
        for (det in output) {
            if (det.size < 6) continue

            val xCenter = det[0]
            val yCenter = det[1]
            val width = det[2]
            val height = det[3]
            val confidence = det[4]
            // det[5] = class_id (0 = person)

            if (confidence > CONFIDENCE_THRESHOLD) {
                // Convert from 640x640 to original image coordinates
                val scaleX = origWidth.toFloat() / INPUT_SIZE
                val scaleY = origHeight.toFloat() / INPUT_SIZE

                val x1 = ((xCenter - width / 2f) * scaleX).coerceIn(0f, origWidth.toFloat())
                val y1 = ((yCenter - height / 2f) * scaleY).coerceIn(0f, origHeight.toFloat())
                val x2 = ((xCenter + width / 2f) * scaleX).coerceIn(0f, origWidth.toFloat())
                val y2 = ((yCenter + height / 2f) * scaleY).coerceIn(0f, origHeight.toFloat())

                detections.add(Detection(
                    className = CLASS_NAME,
                    confidence = confidence,
                    boundingBox = RectF(x1, y1, x2, y2)
                ))
            }
        }

        Log.d(TAG, "Detected ${detections.size} people")
        return detections
    }

    fun close() {
        session.close()
        env.close()
    }
}
