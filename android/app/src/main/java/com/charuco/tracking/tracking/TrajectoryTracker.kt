package com.charuco.tracking.tracking

import com.charuco.tracking.utils.PoseData
import com.charuco.tracking.utils.TrajectoryData

/**
 * Tracks camera trajectory over time
 */
class TrajectoryTracker {
    private val poses = mutableListOf<PoseData>()
    private var startTime: Double = 0.0
    private var isTracking = false

    /**
     * Start tracking
     */
    fun start() {
        clear()
        isTracking = true
        startTime = System.currentTimeMillis() / 1000.0
    }

    /**
     * Stop tracking
     */
    fun stop(): TrajectoryData? {
        if (!isTracking || poses.isEmpty()) {
            return null
        }

        isTracking = false
        val endTime = System.currentTimeMillis() / 1000.0

        // Calculate total displacement
        val firstPose = poses.first()
        val lastPose = poses.last()
        val totalDisplacement = lastPose.displacementFrom(firstPose)

        return TrajectoryData(
            poses = poses.toList(),
            startTime = startTime,
            endTime = endTime,
            totalDisplacement = totalDisplacement
        )
    }

    /**
     * Add a pose to the trajectory
     */
    fun addPose(pose: PoseData) {
        if (isTracking) {
            poses.add(pose)
        }
    }

    /**
     * Get current number of poses
     */
    fun getNumPoses(): Int = poses.size

    /**
     * Check if currently tracking
     */
    fun isTracking(): Boolean = isTracking

    /**
     * Get the last recorded pose
     */
    fun getLastPose(): PoseData? = poses.lastOrNull()

    /**
     * Clear all recorded poses
     */
    fun clear() {
        poses.clear()
        startTime = 0.0
    }
}
