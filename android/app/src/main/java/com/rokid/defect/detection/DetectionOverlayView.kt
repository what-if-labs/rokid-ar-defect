package com.rokid.defect.detection

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View

class DetectionOverlayView(context: Context, attrs: AttributeSet? = null) : View(context, attrs) {

    private var detections: List<Detection> = emptyList()
    private var imageWidth: Int = 1
    private var imageHeight: Int = 1

    private val boxPaint = Paint().apply {
        style = Paint.Style.STROKE
        strokeWidth = 6f
        isAntiAlias = true
    }

    private val textPaint = Paint().apply {
        color = Color.WHITE
        textSize = 36f
        isAntiAlias = true
        isFakeBoldText = true
    }

    private val backgroundPaint = Paint().apply {
        style = Paint.Style.FILL
    }

    fun setDetections(detections: List<Detection>, imageWidth: Int = 1, imageHeight: Int = 1) {
        this.detections = detections
        this.imageWidth = imageWidth
        this.imageHeight = imageHeight
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        // Detections are in original image coordinates; map to view coordinates
        val scaleX = width.toFloat() / imageWidth.toFloat().coerceAtLeast(1f)
        val scaleY = height.toFloat() / imageHeight.toFloat().coerceAtLeast(1f)

        for (detection in detections) {
            val box = detection.boundingBox

            // Green = high confidence, yellow = medium, orange = low
            val color = when {
                detection.confidence > 0.8f -> Color.rgb(0, 255, 100)
                detection.confidence > 0.6f -> Color.YELLOW
                else -> Color.rgb(255, 165, 0)
            }

            boxPaint.color = color
            backgroundPaint.color = Color.argb(180, Color.red(color), Color.green(color), Color.blue(color))

            // Draw bounding box
            canvas.drawRect(
                box.left * scaleX,
                box.top * scaleY,
                box.right * scaleX,
                box.bottom * scaleY,
                boxPaint
            )

            // Draw label
            val label = "${detection.className} ${String.format("%.0f", detection.confidence * 100)}%"
            val textBounds = android.graphics.Rect()
            textPaint.getTextBounds(label, 0, label.length, textBounds)

            canvas.drawRect(
                box.left * scaleX,
                box.top * scaleY - textBounds.height() - 12,
                box.left * scaleX + textBounds.width() + 24,
                box.top * scaleY,
                backgroundPaint
            )

            canvas.drawText(
                label,
                box.left * scaleX + 12,
                box.top * scaleY - 12,
                textPaint
            )
        }
    }
}
