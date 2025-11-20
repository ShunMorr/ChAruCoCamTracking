package com.charuco.tracking.calibration

import com.charuco.tracking.utils.ConfigManager
import org.opencv.aruco.Aruco
import org.opencv.aruco.CharucoBoard
import org.opencv.aruco.DetectorParameters
import org.opencv.aruco.Dictionary
import org.opencv.calib3d.Calib3d
import org.opencv.core.*
import org.opencv.imgproc.Imgproc

/**
 * Camera calibration using ChArUco board
 */
class CameraCalibrator(private val configManager: ConfigManager) {
    private val dictionary: Dictionary
    private val board: CharucoBoard
    private val detectorParams: DetectorParameters

    private val allCharucoCorners = mutableListOf<Mat>()
    private val allCharucoIds = mutableListOf<Mat>()
    private val allImagePoints = mutableListOf<Mat>()
    private val allObjectPoints = mutableListOf<Mat>()

    private var imageSize: Size? = null

    init {
        // Setup ArUco dictionary
        val dictName = configManager.getDictionary()
        val dictId = when (dictName) {
            "DICT_4X4_50" -> Aruco.DICT_4X4_50
            "DICT_5X5_100" -> Aruco.DICT_5X5_100
            "DICT_6X6_250" -> Aruco.DICT_6X6_250
            "DICT_7X7_1000" -> Aruco.DICT_7X7_1000
            else -> Aruco.DICT_5X5_100
        }
        dictionary = Aruco.getPredefinedDictionary(dictId)

        // Create ChArUco board
        val squaresX = configManager.getSquaresX()
        val squaresY = configManager.getSquaresY()
        val squareLength = configManager.getSquareLength().toFloat()
        val markerLength = configManager.getMarkerLength().toFloat()

        board = CharucoBoard.create(
            squaresX,
            squaresY,
            squareLength,
            markerLength,
            dictionary
        )

        // Setup detector parameters
        detectorParams = DetectorParameters.create().apply {
            cornerRefinementMethod = Aruco.CORNER_REFINE_SUBPIX
            cornerRefinementWinSize = 5
            cornerRefinementMaxIterations = 30
            cornerRefinementMinAccuracy = 0.01
        }
    }

    /**
     * Capture a calibration frame
     */
    fun captureFrame(frame: Mat): Boolean {
        if (imageSize == null) {
            imageSize = frame.size()
        }

        val gray = Mat()
        Imgproc.cvtColor(frame, gray, Imgproc.COLOR_BGR2GRAY)

        // Detect ArUco markers
        val markerCorners = mutableListOf<Mat>()
        val markerIds = Mat()
        val rejectedCandidates = mutableListOf<Mat>()

        Aruco.detectMarkers(gray, dictionary, markerCorners, markerIds, detectorParams, rejectedCandidates)

        if (markerIds.empty() || markerCorners.isEmpty()) {
            gray.release()
            markerIds.release()
            return false
        }

        // Interpolate ChArUco corners
        val charucoCorners = Mat()
        val charucoIds = Mat()

        val numInterpolated = Aruco.interpolateCornersCharuco(
            markerCorners,
            markerIds,
            gray,
            board,
            charucoCorners,
            charucoIds
        )

        gray.release()
        markerCorners.forEach { it.release() }
        markerIds.release()

        if (numInterpolated < 4) {
            charucoCorners.release()
            charucoIds.release()
            return false
        }

        // Store the corners
        allCharucoCorners.add(charucoCorners.clone())
        allCharucoIds.add(charucoIds.clone())

        charucoCorners.release()
        charucoIds.release()

        return true
    }

    /**
     * Get number of captured frames
     */
    fun getNumFrames(): Int = allCharucoCorners.size

    /**
     * Perform camera calibration
     */
    fun calibrate(): CalibrationResult? {
        val minFrames = configManager.getMinCalibrationFrames()
        if (allCharucoCorners.size < minFrames) {
            return null
        }

        val imgSize = imageSize ?: return null

        // Prepare object and image points for calibration
        for (i in allCharucoCorners.indices) {
            val objPoints = Mat()
            val imgPoints = Mat()

            board.matchImagePoints(allCharucoCorners[i], allCharucoIds[i], objPoints, imgPoints)

            allObjectPoints.add(objPoints)
            allImagePoints.add(imgPoints)
        }

        // Initialize camera matrix
        val cameraMatrix = Mat.eye(3, 3, CvType.CV_64F)
        val distCoeffs = Mat.zeros(5, 1, CvType.CV_64F)

        val rvecs = mutableListOf<Mat>()
        val tvecs = mutableListOf<Mat>()

        // Perform calibration
        val reprojectionError = Calib3d.calibrateCamera(
            allObjectPoints,
            allImagePoints,
            imgSize,
            cameraMatrix,
            distCoeffs,
            rvecs,
            tvecs,
            Calib3d.CALIB_RATIONAL_MODEL
        )

        // Clean up
        rvecs.forEach { it.release() }
        tvecs.forEach { it.release() }

        return CalibrationResult(
            cameraMatrix = cameraMatrix,
            distCoeffs = distCoeffs,
            reprojectionError = reprojectionError,
            numFrames = allCharucoCorners.size
        )
    }

    /**
     * Clear all captured frames
     */
    fun clear() {
        allCharucoCorners.forEach { it.release() }
        allCharucoIds.forEach { it.release() }
        allObjectPoints.forEach { it.release() }
        allImagePoints.forEach { it.release() }

        allCharucoCorners.clear()
        allCharucoIds.clear()
        allObjectPoints.clear()
        allImagePoints.clear()
    }

    /**
     * Draw detection on frame for visualization
     */
    fun drawDetection(frame: Mat): Boolean {
        val gray = Mat()
        Imgproc.cvtColor(frame, gray, Imgproc.COLOR_BGR2GRAY)

        // Detect ArUco markers
        val markerCorners = mutableListOf<Mat>()
        val markerIds = Mat()
        val rejectedCandidates = mutableListOf<Mat>()

        Aruco.detectMarkers(gray, dictionary, markerCorners, markerIds, detectorParams, rejectedCandidates)

        var detected = false

        if (!markerIds.empty() && markerCorners.isNotEmpty()) {
            // Draw detected markers
            Aruco.drawDetectedMarkers(frame, markerCorners, markerIds)

            // Interpolate ChArUco corners
            val charucoCorners = Mat()
            val charucoIds = Mat()

            val numInterpolated = Aruco.interpolateCornersCharuco(
                markerCorners,
                markerIds,
                gray,
                board,
                charucoCorners,
                charucoIds
            )

            if (numInterpolated >= 4) {
                // Draw ChArUco corners
                Aruco.drawDetectedCornersCharuco(
                    frame,
                    charucoCorners,
                    charucoIds,
                    Scalar(0.0, 255.0, 0.0)
                )
                detected = true
            }

            charucoCorners.release()
            charucoIds.release()
        }

        gray.release()
        markerCorners.forEach { it.release() }
        markerIds.release()

        return detected
    }

    data class CalibrationResult(
        val cameraMatrix: Mat,
        val distCoeffs: Mat,
        val reprojectionError: Double,
        val numFrames: Int
    )
}
