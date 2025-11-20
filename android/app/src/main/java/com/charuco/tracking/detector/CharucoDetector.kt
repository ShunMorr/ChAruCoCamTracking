package com.charuco.tracking.detector

import com.charuco.tracking.utils.CalibrationManager
import com.charuco.tracking.utils.ConfigManager
import com.charuco.tracking.utils.PoseData
import org.opencv.aruco.Aruco
import org.opencv.aruco.CharucoBoard
import org.opencv.aruco.DetectorParameters
import org.opencv.aruco.Dictionary
import org.opencv.calib3d.Calib3d
import org.opencv.core.*
import org.opencv.imgproc.Imgproc
import kotlin.math.*

/**
 * ChArUco board detector and pose estimator
 */
class CharucoDetector(
    private val configManager: ConfigManager,
    private val calibrationData: CalibrationManager.CalibrationData
) {
    private val dictionary: Dictionary
    private val board: CharucoBoard
    private val detectorParams: DetectorParameters
    private val cameraMatrix: Mat
    private val distCoeffs: Mat

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

        // Setup detector parameters for high precision
        detectorParams = DetectorParameters.create().apply {
            cornerRefinementMethod = Aruco.CORNER_REFINE_SUBPIX
            cornerRefinementWinSize = 5
            cornerRefinementMaxIterations = 30
            cornerRefinementMinAccuracy = 0.01
        }

        // Camera calibration parameters
        cameraMatrix = calibrationData.cameraMatrix
        distCoeffs = calibrationData.distCoeffs
    }

    /**
     * Detect ChArUco board and estimate pose
     */
    fun detectAndEstimatePose(frame: Mat): DetectionResult? {
        val gray = Mat()
        Imgproc.cvtColor(frame, gray, Imgproc.COLOR_BGR2GRAY)

        // Detect ArUco markers
        val markerCorners = mutableListOf<Mat>()
        val markerIds = Mat()
        val rejectedCandidates = mutableListOf<Mat>()

        Aruco.detectMarkers(gray, dictionary, markerCorners, markerIds, detectorParams, rejectedCandidates)

        if (markerIds.empty() || markerCorners.isEmpty()) {
            gray.release()
            return null
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
            charucoIds,
            cameraMatrix,
            distCoeffs
        )

        gray.release()
        markerCorners.forEach { it.release() }

        if (numInterpolated < 4) {
            charucoCorners.release()
            charucoIds.release()
            markerIds.release()
            return null
        }

        // Estimate pose
        val rvec = Mat()
        val tvec = Mat()
        val success = Aruco.estimatePoseCharucoBoard(
            charucoCorners,
            charucoIds,
            board,
            cameraMatrix,
            distCoeffs,
            rvec,
            tvec
        )

        if (!success) {
            charucoCorners.release()
            charucoIds.release()
            markerIds.release()
            rvec.release()
            tvec.release()
            return null
        }

        // Convert to PoseData
        val poseData = convertToPoseData(rvec, tvec, charucoCorners, charucoIds)

        return DetectionResult(
            poseData = poseData,
            rvec = rvec,
            tvec = tvec,
            charucoCorners = charucoCorners,
            charucoIds = charucoIds,
            numCorners = numInterpolated
        )
    }

    /**
     * Convert rotation and translation vectors to PoseData
     */
    private fun convertToPoseData(
        rvec: Mat,
        tvec: Mat,
        charucoCorners: Mat,
        charucoIds: Mat
    ): PoseData {
        // Translation (convert meters to mm)
        val x = tvec.get(0, 0)[0] * 1000.0
        val y = tvec.get(1, 0)[0] * 1000.0
        val z = tvec.get(2, 0)[0] * 1000.0

        // Convert rotation vector to Euler angles
        val rotMat = Mat()
        Calib3d.Rodrigues(rvec, rotMat)

        val (roll, pitch, yaw) = rotationMatrixToEulerAngles(rotMat)
        rotMat.release()

        // Calculate quality score
        val quality = getPoseQualityScore(charucoCorners, charucoIds)

        return PoseData(
            translation = PoseData.Translation(x, y, z),
            rotation = PoseData.Rotation(
                roll = Math.toDegrees(roll),
                pitch = Math.toDegrees(pitch),
                yaw = Math.toDegrees(yaw)
            ),
            quality = quality,
            numCorners = charucoCorners.rows()
        )
    }

    /**
     * Convert rotation matrix to Euler angles (ZYX convention)
     */
    private fun rotationMatrixToEulerAngles(R: Mat): Triple<Double, Double, Double> {
        val sy = sqrt(R.get(0, 0)[0] * R.get(0, 0)[0] + R.get(1, 0)[0] * R.get(1, 0)[0])

        val singular = sy < 1e-6

        val roll: Double
        val pitch: Double
        val yaw: Double

        if (!singular) {
            roll = atan2(R.get(2, 1)[0], R.get(2, 2)[0])
            pitch = atan2(-R.get(2, 0)[0], sy)
            yaw = atan2(R.get(1, 0)[0], R.get(0, 0)[0])
        } else {
            roll = atan2(-R.get(1, 2)[0], R.get(1, 1)[0])
            pitch = atan2(-R.get(2, 0)[0], sy)
            yaw = 0.0
        }

        return Triple(roll, pitch, yaw)
    }

    /**
     * Calculate pose quality score based on number of detected corners
     */
    private fun getPoseQualityScore(charucoCorners: Mat, charucoIds: Mat): Double {
        val totalCorners = (configManager.getSquaresX() - 1) * (configManager.getSquaresY() - 1)
        val detectedCorners = charucoCorners.rows()
        return minOf(detectedCorners.toDouble() / totalCorners.toDouble(), 1.0)
    }

    /**
     * Draw detection visualization on frame
     */
    fun drawDetection(
        frame: Mat,
        detectionResult: DetectionResult
    ) {
        // Draw detected corners
        if (!detectionResult.charucoCorners.empty()) {
            Aruco.drawDetectedCornersCharuco(
                frame,
                detectionResult.charucoCorners,
                detectionResult.charucoIds,
                Scalar(0.0, 255.0, 0.0)
            )
        }

        // Draw coordinate axes
        val axisLength = (configManager.getSquareLength() * 2).toFloat()
        Aruco.drawAxis(
            frame,
            cameraMatrix,
            distCoeffs,
            detectionResult.rvec,
            detectionResult.tvec,
            axisLength
        )
    }

    /**
     * Result of ChArUco detection
     */
    data class DetectionResult(
        val poseData: PoseData,
        val rvec: Mat,
        val tvec: Mat,
        val charucoCorners: Mat,
        val charucoIds: Mat,
        val numCorners: Int
    ) {
        fun release() {
            rvec.release()
            tvec.release()
            charucoCorners.release()
            charucoIds.release()
        }
    }

    /**
     * Generate ChArUco board image
     */
    fun generateBoardImage(imageSize: Int): Mat {
        val boardImage = Mat()
        board.draw(Size(imageSize.toDouble(), imageSize.toDouble()), boardImage, 10, 1)
        return boardImage
    }
}
