package com.charuco.tracking.utils

import org.yaml.snakeyaml.Yaml
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.*

/**
 * Export measurement data to YAML format
 */
class DataExporter {
    private val yaml = Yaml()
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())

    /**
     * Export spot measurement to YAML file
     */
    fun exportSpotMeasurement(measurement: SpotMeasurement, file: File) {
        val data = mutableMapOf<String, Any>()

        // Metadata
        data["metadata"] = mapOf(
            "timestamp" to dateFormat.format(Date()),
            "measurement_type" to "spot"
        )

        // Pose data
        val pose = measurement.pose
        data["pose"] = mapOf(
            "translation" to mapOf(
                "x" to pose.translation.x,
                "y" to pose.translation.y,
                "z" to pose.translation.z
            ),
            "rotation" to mapOf(
                "roll" to pose.rotation.roll,
                "pitch" to pose.rotation.pitch,
                "yaw" to pose.rotation.yaw
            ),
            "quality" to pose.quality,
            "num_samples" to measurement.numSamples,
            "std_dev" to mapOf(
                "x_mm" to measurement.stdDev.xMm,
                "y_mm" to measurement.stdDev.yMm,
                "z_mm" to measurement.stdDev.zMm
            )
        )

        FileWriter(file).use { writer ->
            yaml.dump(data, writer)
        }
    }

    /**
     * Export trajectory to YAML file
     */
    fun exportTrajectory(trajectory: TrajectoryData, file: File) {
        val data = mutableMapOf<String, Any>()

        // Metadata
        data["metadata"] = mapOf(
            "num_poses" to trajectory.numPoses,
            "duration_sec" to trajectory.durationSec,
            "timestamp" to dateFormat.format(Date())
        )

        // Trajectory poses
        val posesList = trajectory.poses.map { pose ->
            mapOf(
                "timestamp" to pose.timestamp,
                "translation" to mapOf(
                    "x" to pose.translation.x,
                    "y" to pose.translation.y,
                    "z" to pose.translation.z
                ),
                "rotation" to mapOf(
                    "roll" to pose.rotation.roll,
                    "pitch" to pose.rotation.pitch,
                    "yaw" to pose.rotation.yaw
                ),
                "quality" to pose.quality,
                "num_corners" to pose.numCorners
            )
        }
        data["trajectory"] = posesList

        // Total displacement
        val disp = trajectory.totalDisplacement
        data["total_displacement"] = mapOf(
            "displacement" to mapOf(
                "x_mm" to disp.xMm,
                "y_mm" to disp.yMm,
                "z_mm" to disp.zMm,
                "yaw_deg" to disp.yawDeg
            ),
            "distance_2d_mm" to disp.distance2DMm,
            "distance_3d_mm" to disp.distance3DMm
        )

        FileWriter(file).use { writer ->
            yaml.dump(data, writer)
        }
    }

    /**
     * Export displacement comparison to YAML file
     */
    fun exportDisplacement(
        displacement: PoseData.Displacement,
        file1Name: String,
        file2Name: String,
        comparisonType: String,
        file: File
    ) {
        val data = mutableMapOf<String, Any>()

        // Metadata
        data["metadata"] = mapOf(
            "comparison_type" to comparisonType,
            "file1" to file1Name,
            "file2" to file2Name,
            "timestamp" to dateFormat.format(Date())
        )

        // Displacement
        data["displacement"] = mapOf(
            "displacement" to mapOf(
                "x_mm" to displacement.xMm,
                "y_mm" to displacement.yMm,
                "z_mm" to displacement.zMm,
                "yaw_deg" to displacement.yawDeg
            ),
            "distance_2d_mm" to displacement.distance2DMm,
            "distance_3d_mm" to displacement.distance3DMm
        )

        FileWriter(file).use { writer ->
            yaml.dump(data, writer)
        }
    }
}
