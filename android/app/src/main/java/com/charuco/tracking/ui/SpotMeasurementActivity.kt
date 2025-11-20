package com.charuco.tracking.ui

import android.app.AlertDialog
import android.os.Bundle
import android.os.Environment
import android.util.Log
import android.view.View
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import com.charuco.tracking.R
import com.charuco.tracking.databinding.ActivitySpotMeasurementBinding
import com.charuco.tracking.detector.CharucoDetector
import com.charuco.tracking.tracking.SpotMeasurer
import com.charuco.tracking.utils.CalibrationManager
import com.charuco.tracking.utils.ConfigManager
import com.charuco.tracking.utils.DataExporter
import com.charuco.tracking.utils.SpotMeasurement
import org.opencv.android.Utils
import org.opencv.core.Mat
import java.io.File
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class SpotMeasurementActivity : AppCompatActivity() {
    private lateinit var binding: ActivitySpotMeasurementBinding
    private lateinit var cameraExecutor: ExecutorService
    private lateinit var detector: CharucoDetector
    private lateinit var measurer: SpotMeasurer
    private lateinit var configManager: ConfigManager
    private lateinit var dataExporter: DataExporter

    private var imageAnalysis: ImageAnalysis? = null
    private var camera: Camera? = null
    private var completedMeasurement: SpotMeasurement? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySpotMeasurementBinding.inflate(layoutInflater)
        setContentView(binding.root)

        configManager = ConfigManager(this)
        val calibrationManager = CalibrationManager(this)
        val calibrationData = calibrationManager.loadCalibration()

        if (calibrationData == null) {
            Toast.makeText(this, "キャリブレーションデータが見つかりません", Toast.LENGTH_LONG).show()
            finish()
            return
        }

        detector = CharucoDetector(configManager, calibrationData)
        measurer = SpotMeasurer(targetSamples = 30)
        dataExporter = DataExporter()

        cameraExecutor = Executors.newSingleThreadExecutor()

        setupUI()
        startCamera()
    }

    private fun setupUI() {
        updateUI()

        binding.btnStartMeasurement.setOnClickListener {
            if (!measurer.isMeasuring()) {
                startMeasurement()
            }
        }
    }

    private fun startMeasurement() {
        measurer.start()
        binding.btnStartMeasurement.isEnabled = false
        binding.resultContainer.visibility = View.GONE
        Toast.makeText(this, "測定開始", Toast.LENGTH_SHORT).show()
    }

    private fun onMeasurementComplete(measurement: SpotMeasurement) {
        completedMeasurement = measurement
        binding.btnStartMeasurement.isEnabled = true
        binding.resultContainer.visibility = View.VISIBLE

        // Display results
        val pose = measurement.pose
        binding.tvPosition.text = "位置: X=%.2fmm, Y=%.2fmm, Z=%.2fmm".format(
            pose.translation.x,
            pose.translation.y,
            pose.translation.z
        )
        binding.tvRotation.text = "回転: Yaw=%.2f°".format(pose.rotation.yaw)
        binding.tvStdDev.text = "標準偏差: X=%.4fmm, Y=%.4fmm, Z=%.4fmm".format(
            measurement.stdDev.xMm,
            measurement.stdDev.yMm,
            measurement.stdDev.zMm
        )

        Toast.makeText(this, getString(R.string.measurement_complete), Toast.LENGTH_SHORT).show()

        // Show save dialog
        showSaveDialog(measurement)
    }

    private fun showSaveDialog(measurement: SpotMeasurement) {
        val input = EditText(this)
        input.hint = "ファイル名 (例: spot_before)"

        AlertDialog.Builder(this)
            .setTitle(getString(R.string.save_measurement))
            .setView(input)
            .setPositiveButton(getString(R.string.save)) { _, _ ->
                val fileName = input.text.toString().trim()
                if (fileName.isNotEmpty()) {
                    saveMeasurement(measurement, fileName)
                }
            }
            .setNegativeButton(getString(R.string.cancel), null)
            .show()
    }

    private fun saveMeasurement(measurement: SpotMeasurement, fileName: String) {
        try {
            val file = File(
                getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS),
                "$fileName.yaml"
            )
            dataExporter.exportSpotMeasurement(measurement, file)
            Toast.makeText(
                this,
                "測定結果を保存しました: ${file.absolutePath}",
                Toast.LENGTH_LONG
            ).show()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to save measurement", e)
            Toast.makeText(this, getString(R.string.error_saving_file), Toast.LENGTH_LONG).show()
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
                    it.setAnalyzer(cameraExecutor, MeasurementAnalyzer())
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

    private inner class MeasurementAnalyzer : ImageAnalysis.Analyzer {
        @androidx.camera.core.ExperimentalGetImage
        override fun analyze(imageProxy: ImageProxy) {
            val mediaImage = imageProxy.image
            if (mediaImage != null) {
                val bitmap = imageProxy.toBitmap()
                val mat = Mat()
                Utils.bitmapToMat(bitmap, mat)

                val detectionResult = detector.detectAndEstimatePose(mat)

                if (detectionResult != null) {
                    // Add sample if measuring
                    if (measurer.isMeasuring()) {
                        val isComplete = measurer.addSample(detectionResult.poseData)

                        runOnUiThread {
                            updateUI()
                        }

                        if (isComplete) {
                            val measurement = measurer.stop()
                            if (measurement != null) {
                                runOnUiThread {
                                    onMeasurementComplete(measurement)
                                }
                            }
                        }
                    }

                    detectionResult.release()
                }

                mat.release()
            }
            imageProxy.close()
        }
    }

    private fun updateUI() {
        if (measurer.isMeasuring()) {
            val numSamples = measurer.getNumSamples()
            val targetSamples = measurer.getTargetSamples()
            val progress = measurer.getProgress()

            binding.tvSampleCount.text = getString(
                R.string.samples_collected,
                numSamples,
                targetSamples,
                progress
            )
        } else {
            binding.tvSampleCount.text = "測定待機中"
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }

    companion object {
        private const val TAG = "SpotMeasurementActivity"
    }
}
