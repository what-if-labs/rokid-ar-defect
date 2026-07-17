package com.rokid.defect.detection

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View

class DetectionOverlayView(context: Context, attrs: AttributeSet? = null) : View(context, attrs) {

    private var detections: List<Detection> = emptyList()
    
    private val boxPaint = Paint().apply {
        style = Paint.Style.STROKE
        strokeWidth = 4f
        isAntiAlias = true
    }
    
    private val textPaint = Paint().apply {
        color = Color.WHITE
        textSize = 32f
        isAntiAlias = true
        isFakeBoldText = true
    }
    
    private val backgroundPaint = Paint().apply {
        style = Paint.Style.FILL
    }

    fun setDetections(detections: List<Detection>) {
        this.detections = detections
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        
        val scaleX = width.toFloat() / 640f
        val scaleY = height.toFloat() / 640f
        
        for (detection in detections) {
            val box = detection.boundingBox
            
            // Color based on confidence
            val color = when {
                detection.confidence > 0.9f -> Color.GREEN
                detection.confidence > 0.7f -> Color.YELLOW
                else -> Color.RED
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
            
            // Draw label background
            val label = "${detection.className} ${String.format("%.1f", detection.confidence * 100)}%"
            val textBounds = android.graphics.Rect()
            textPaint.getTextBounds(label, 0, label.length, textBounds)
            
            canvas.drawRect(
                box.left * scaleX,
                box.top * scaleY - textBounds.height() - 10,
                box.left * scaleX + textBounds.width() + 20,
                box.top * scaleY,
                backgroundPaint
            )
            
            // Draw label text
            canvas.drawText(
                label,
                box.left * scaleX + 10,
                box.top * scaleY - 10,
                textPaint
            )
        }
    }
}
