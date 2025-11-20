package com.charuco.tracking.tracking

import com.charuco.tracking.utils.PoseData
import com.charuco.tracking.utils.SpotMeasurement
import kotlin.math.sqrt

/**
 * Performs spot measurement with multiple samples and averaging
 */
class SpotMeasurer(private val targetSamples: Int = 30) {
    private val samples = mutableListOf<PoseData>()
    private var isMeasuring = false

    /**
     * Start measurement
     */
    fun start() {
        clear()
        isMeasuring = true
    }

    /**
     * Stop measurement and calculate result
     */
    fun stop(): SpotMeasurement? {
        if (!isMeasuring || samples.isEmpty()) {
            return null
        }

        isMeasuring = false
        return calculateMeasurement()
    }

    /**
     * Add a sample pose
     */
    fun addSample(pose: PoseData): Boolean {
        if (!isMeasuring) {
            return false
        }

        samples.add(pose)
        return samples.size >= targetSamples
    }

    /**
     * Get current number of samples
     */
    fun getNumSamples(): Int = samples.size

    /**
     * Get target number of samples
     */
    fun getTargetSamples(): Int = targetSamples

    /**
     * Get progress percentage
     */
    fun getProgress(): Double = (samples.size.toDouble() / targetSamples.toDouble()) * 100.0

    /**
     * Check if measurement is complete
     */
    fun isComplete(): Boolean = samples.size >= targetSamples

    /**
     * Check if currently measuring
     */
    fun isMeasuring(): Boolean = isMeasuring

    /**
     * Calculate spot measurement from samples
     */
    private fun calculateMeasurement(): SpotMeasurement {
        // Calculate mean
        val meanX = samples.map { it.translation.x }.average()
        val meanY = samples.map { it.translation.y }.average()
        val meanZ = samples.map { it.translation.z }.average()
        val meanRoll = samples.map { it.rotation.roll }.average()
        val meanPitch = samples.map { it.rotation.pitch }.average()
        val meanYaw = samples.map { it.rotation.yaw }.average()
        val meanQuality = samples.map { it.quality }.average()
        val meanCorners = samples.map { it.numCorners }.average().toInt()

        // Calculate standard deviation
        val stdDevX = calculateStdDev(samples.map { it.translation.x }, meanX)
        val stdDevY = calculateStdDev(samples.map { it.translation.y }, meanY)
        val stdDevZ = calculateStdDev(samples.map { it.translation.z }, meanZ)

        val avgPose = PoseData(
            translation = PoseData.Translation(meanX, meanY, meanZ),
            rotation = PoseData.Rotation(meanRoll, meanPitch, meanYaw),
            quality = meanQuality,
            numCorners = meanCorners
        )

        return SpotMeasurement(
            pose = avgPose,
            numSamples = samples.size,
            stdDev = SpotMeasurement.StdDev(stdDevX, stdDevY, stdDevZ)
        )
    }

    /**
     * Calculate standard deviation
     */
    private fun calculateStdDev(values: List<Double>, mean: Double): Double {
        if (values.size <= 1) {
            return 0.0
        }

        val variance = values.map { (it - mean) * (it - mean) }.average()
        return sqrt(variance)
    }

    /**
     * Clear all samples
     */
    fun clear() {
        samples.clear()
    }
}
