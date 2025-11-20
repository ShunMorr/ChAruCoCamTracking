package com.charuco.tracking.ui

import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import com.charuco.tracking.R
import com.charuco.tracking.calibration.CameraCalibrator
import com.charuco.tracking.databinding.ActivityCalibrationBinding
import com.charuco.tracking.utils.CalibrationManager
import com.charuco.tracking.utils.ConfigManager
import org.opencv.android.Utils
import org.opencv.core.Mat
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class CalibrationActivity : AppCompatActivity() {
    private lateinit var binding: ActivityCalibrationBinding
    private lateinit var cameraExecutor: ExecutorService
    private lateinit var calibrator: CameraCalibrator
    private lateinit var calibrationManager: CalibrationManager
    private lateinit var configManager: ConfigManager

    private var imageAnalysis: ImageAnalysis? = null
    private var camera: Camera? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCalibrationBinding.inflate(layoutInflater)
        setContentView(binding.root)

        configManager = ConfigManager(this)
        calibrationManager = CalibrationManager(this)
        calibrator = CameraCalibrator(configManager)

        cameraExecutor = Executors.newSingleThreadExecutor()

        setupUI()
        startCamera()
    }

    private fun setupUI() {
        updateFrameCount()

        binding.btnCaptureFrame.setOnClickListener {
            // Frame capture will be triggered
            Toast.makeText(this, "フレームをキャプチャ中...", Toast.LENGTH_SHORT).show()
        }

        binding.btnCalibrate.setOnClickListener {
            performCalibration()
        }
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)

        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder()
                .build()
                .also {
                    it.setSurfaceProvider(binding.previewView.surfaceProvider)
                }

            imageAnalysis = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor, CalibrationAnalyzer())
                }

            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

            try {
                cameraProvider.unbindAll()
                camera = cameraProvider.bindToLifecycle(
                    this,
                    cameraSelector,
                    preview,
                    imageAnalysis
                )
            } catch (e: Exception) {
                Log.e(TAG, "Camera binding failed", e)
            }

        }, ContextCompat.getMainExecutor(this))
    }

    private inner class CalibrationAnalyzer : ImageAnalysis.Analyzer {
        private var lastCaptureTime = 0L
        private val captureInterval = 500L // ms

        @androidx.camera.core.ExperimentalGetImage
        override fun analyze(imageProxy: ImageProxy) {
            val mediaImage = imageProxy.image
            if (mediaImage != null) {
                val bitmap = imageProxy.toBitmap()
                val mat = Mat()
                Utils.bitmapToMat(bitmap, mat)

                // Draw detection on UI thread
                runOnUiThread {
                    calibrator.drawDetection(mat)
                }

                // Auto-capture frames if button is held
                val currentTime = System.currentTimeMillis()
                if (binding.btnCaptureFrame.isPressed &&
                    currentTime - lastCaptureTime > captureInterval
                ) {
                    if (calibrator.captureFrame(mat)) {
                        lastCaptureTime = currentTime
                        runOnUiThread {
                            updateFrameCount()
                            Toast.makeText(
                                this@CalibrationActivity,
                                "フレーム取得成功",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    }
                }

                mat.release()
            }
            imageProxy.close()
        }
    }

    private fun updateFrameCount() {
        val numFrames = calibrator.getNumFrames()
        val minFrames = configManager.getMinCalibrationFrames()

        binding.tvFrameCount.text = getString(R.string.frames_collected, numFrames, minFrames)

        // Enable calibration button if enough frames
        binding.btnCalibrate.isEnabled = numFrames >= minFrames
    }

    private fun performCalibration() {
        binding.btnCalibrate.isEnabled = false
        Toast.makeText(this, "キャリブレーション実行中...", Toast.LENGTH_SHORT).show()

        cameraExecutor.execute {
            val result = calibrator.calibrate()

            runOnUiThread {
                if (result != null) {
                    calibrationManager.saveCalibration(
                        result.cameraMatrix,
                        result.distCoeffs,
                        result.reprojectionError
                    )

                    binding.tvReprojectionError.text =
                        getString(R.string.reprojection_error, result.reprojectionError)
                    binding.tvReprojectionError.visibility = View.VISIBLE

                    Toast.makeText(
                        this,
                        getString(R.string.calibration_success),
                        Toast.LENGTH_LONG
                    ).show()

                    // Finish activity after short delay
                    binding.root.postDelayed({ finish() }, 2000)
                } else {
                    Toast.makeText(
                        this,
                        getString(R.string.calibration_error),
                        Toast.LENGTH_LONG
                    ).show()
                    binding.btnCalibrate.isEnabled = true
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        calibrator.clear()
    }

    companion object {
        private const val TAG = "CalibrationActivity"
    }
}
