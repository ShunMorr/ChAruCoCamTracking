package com.charuco.tracking.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.charuco.tracking.R
import com.charuco.tracking.databinding.ActivityMainBinding
import com.charuco.tracking.utils.CalibrationManager
import com.charuco.tracking.utils.ConfigManager
import org.opencv.android.OpenCVLoader

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private lateinit var calibrationManager: CalibrationManager
    private lateinit var configManager: ConfigManager

    companion object {
        private const val CAMERA_PERMISSION_REQUEST_CODE = 100
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize OpenCV
        if (!OpenCVLoader.initDebug()) {
            Toast.makeText(this, "OpenCV initialization failed", Toast.LENGTH_LONG).show()
            finish()
            return
        }

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        calibrationManager = CalibrationManager(this)
        configManager = ConfigManager(this)

        setupUI()
        checkCameraPermission()
    }

    private fun setupUI() {
        binding.btnCalibrate.setOnClickListener {
            startActivity(Intent(this, CalibrationActivity::class.java))
        }

        binding.btnTracking.setOnClickListener {
            if (calibrationManager.hasCalibration()) {
                startActivity(Intent(this, TrackingActivity::class.java))
            } else {
                Toast.makeText(this, "カメラキャリブレーションを先に実行してください", Toast.LENGTH_LONG).show()
            }
        }

        binding.btnSpotMeasurement.setOnClickListener {
            if (calibrationManager.hasCalibration()) {
                startActivity(Intent(this, SpotMeasurementActivity::class.java))
            } else {
                Toast.makeText(this, "カメラキャリブレーションを先に実行してください", Toast.LENGTH_LONG).show()
            }
        }

        updateCalibrationStatus()
    }

    private fun updateCalibrationStatus() {
        if (calibrationManager.hasCalibration()) {
            val calibration = calibrationManager.loadCalibration()
            if (calibration != null) {
                binding.tvCalibrationStatus.text =
                    "キャリブレーション済み (再投影誤差: %.3f px)".format(calibration.reprojectionError)
            }
        } else {
            binding.tvCalibrationStatus.text = "キャリブレーションが必要です"
        }
    }

    override fun onResume() {
        super.onResume()
        updateCalibrationStatus()
    }

    private fun checkCameraPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.CAMERA),
                CAMERA_PERMISSION_REQUEST_CODE
            )
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            CAMERA_PERMISSION_REQUEST_CODE -> {
                if (grantResults.isEmpty() || grantResults[0] != PackageManager.PERMISSION_GRANTED) {
                    Toast.makeText(
                        this,
                        getString(R.string.camera_permission_denied),
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }
}
