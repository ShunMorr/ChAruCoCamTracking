package com.charuco.tracking.utils

import android.content.Context
import org.opencv.core.Mat
import org.yaml.snakeyaml.Yaml
import java.io.File
import java.io.FileInputStream
import java.io.FileWriter

/**
 * Manages camera calibration parameters
 */
class CalibrationManager(private val context: Context) {
    companion object {
        private const val CALIBRATION_FILE = "calibration_params.yaml"
    }

    private val calibrationFile: File
        get() = File(context.filesDir, CALIBRATION_FILE)

    /**
     * Save calibration parameters to YAML file
     */
    fun saveCalibration(
        cameraMatrix: Mat,
        distCoeffs: Mat,
        reprojectionError: Double
    ) {
        val data = mutableMapOf<String, Any>()

        // Camera matrix
        val cameraMatrixList = mutableListOf<List<Double>>()
        for (i in 0 until cameraMatrix.rows()) {
            val row = mutableListOf<Double>()
            for (j in 0 until cameraMatrix.cols()) {
                row.add(cameraMatrix.get(i, j)[0])
            }
            cameraMatrixList.add(row)
        }
        data["camera_matrix"] = cameraMatrixList

        // Distortion coefficients
        val distCoeffsList = mutableListOf<Double>()
        for (i in 0 until distCoeffs.rows()) {
            for (j in 0 until distCoeffs.cols()) {
                distCoeffsList.add(distCoeffs.get(i, j)[0])
            }
        }
        data["dist_coeffs"] = distCoeffsList

        // Reprojection error
        data["reprojection_error"] = reprojectionError
        data["timestamp"] = System.currentTimeMillis() / 1000.0

        val yaml = Yaml()
        FileWriter(calibrationFile).use { writer ->
            yaml.dump(data, writer)
        }
    }

    /**
     * Load calibration parameters from YAML file
     */
    fun loadCalibration(): CalibrationData? {
        if (!calibrationFile.exists()) {
            return null
        }

        try {
            val yaml = Yaml()
            val data = FileInputStream(calibrationFile).use { input ->
                yaml.load<Map<String, Any>>(input)
            }

            // Parse camera matrix
            val cameraMatrixList = data["camera_matrix"] as? List<List<Double>> ?: return null
            val cameraMatrix = Mat(3, 3, org.opencv.core.CvType.CV_64F)
            for (i in cameraMatrixList.indices) {
                for (j in cameraMatrixList[i].indices) {
                    cameraMatrix.put(i, j, cameraMatrixList[i][j])
                }
            }

            // Parse distortion coefficients
            val distCoeffsList = data["dist_coeffs"] as? List<Double> ?: return null
            val distCoeffs = Mat(1, distCoeffsList.size, org.opencv.core.CvType.CV_64F)
            for (i in distCoeffsList.indices) {
                distCoeffs.put(0, i, distCoeffsList[i])
            }

            val reprojectionError = (data["reprojection_error"] as? Number)?.toDouble() ?: 0.0

            return CalibrationData(cameraMatrix, distCoeffs, reprojectionError)
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }
    }

    /**
     * Check if calibration file exists
     */
    fun hasCalibration(): Boolean = calibrationFile.exists()

    data class CalibrationData(
        val cameraMatrix: Mat,
        val distCoeffs: Mat,
        val reprojectionError: Double
    )
}
