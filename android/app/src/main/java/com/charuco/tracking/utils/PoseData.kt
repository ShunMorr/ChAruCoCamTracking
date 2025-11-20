package com.charuco.tracking.utils

import org.opencv.core.Mat
import kotlin.math.sqrt

/**
 * Represents a 3D pose with translation and rotation
 */
data class PoseData(
    val translation: Translation,
    val rotation: Rotation,
    val quality: Double,
    val numCorners: Int,
    val timestamp: Double = System.currentTimeMillis() / 1000.0
) {
    data class Translation(
        val x: Double,  // mm
        val y: Double,  // mm
        val z: Double   // mm
    )

    data class Rotation(
        val roll: Double,   // degrees
        val pitch: Double,  // degrees
        val yaw: Double     // degrees
    )

    /**
     * Calculate displacement from another pose
     */
    fun displacementFrom(other: PoseData): Displacement {
        val dx = translation.x - other.translation.x
        val dy = translation.y - other.translation.y
        val dz = translation.z - other.translation.z
        val dyaw = rotation.yaw - other.rotation.yaw

        val distance2D = sqrt(dx * dx + dy * dy)
        val distance3D = sqrt(dx * dx + dy * dy + dz * dz)

        return Displacement(dx, dy, dz, dyaw, distance2D, distance3D)
    }

    data class Displacement(
        val xMm: Double,
        val yMm: Double,
        val zMm: Double,
        val yawDeg: Double,
        val distance2DMm: Double,
        val distance3DMm: Double
    )
}

/**
 * Statistics for spot measurement
 */
data class SpotMeasurement(
    val pose: PoseData,
    val numSamples: Int,
    val stdDev: StdDev
) {
    data class StdDev(
        val xMm: Double,
        val yMm: Double,
        val zMm: Double
    )
}

/**
 * Trajectory data
 */
data class TrajectoryData(
    val poses: List<PoseData>,
    val startTime: Double,
    val endTime: Double,
    val totalDisplacement: PoseData.Displacement
) {
    val numPoses: Int
        get() = poses.size

    val durationSec: Double
        get() = endTime - startTime
}
