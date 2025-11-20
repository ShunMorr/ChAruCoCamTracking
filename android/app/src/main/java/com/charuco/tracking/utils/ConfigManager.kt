package com.charuco.tracking.utils

import android.content.Context
import android.content.SharedPreferences
import org.yaml.snakeyaml.Yaml
import java.io.File
import java.io.FileInputStream

/**
 * Manages application configuration
 */
class ConfigManager(private val context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("charuco_config", Context.MODE_PRIVATE)

    companion object {
        // ChArUco Board Configuration
        const val KEY_DICTIONARY = "dictionary"
        const val KEY_SQUARES_X = "squares_x"
        const val KEY_SQUARES_Y = "squares_y"
        const val KEY_SQUARE_LENGTH = "square_length"
        const val KEY_MARKER_LENGTH = "marker_length"

        // Camera Configuration
        const val KEY_CAMERA_WIDTH = "camera_width"
        const val KEY_CAMERA_HEIGHT = "camera_height"
        const val KEY_CAMERA_FPS = "camera_fps"

        // Tracking Configuration
        const val KEY_TRACKING_FPS = "tracking_fps"
        const val KEY_MIN_CALIBRATION_FRAMES = "min_calibration_frames"

        // Default values
        const val DEFAULT_DICTIONARY = "DICT_5X5_100"
        const val DEFAULT_SQUARES_X = 7
        const val DEFAULT_SQUARES_Y = 7
        const val DEFAULT_SQUARE_LENGTH = 0.04  // meters
        const val DEFAULT_MARKER_LENGTH = 0.03  // meters
        const val DEFAULT_CAMERA_WIDTH = 1280
        const val DEFAULT_CAMERA_HEIGHT = 720
        const val DEFAULT_CAMERA_FPS = 30
        const val DEFAULT_TRACKING_FPS = 10
        const val DEFAULT_MIN_CALIBRATION_FRAMES = 30
    }

    // ChArUco Board Configuration
    fun getDictionary(): String = prefs.getString(KEY_DICTIONARY, DEFAULT_DICTIONARY) ?: DEFAULT_DICTIONARY
    fun getSquaresX(): Int = prefs.getInt(KEY_SQUARES_X, DEFAULT_SQUARES_X)
    fun getSquaresY(): Int = prefs.getInt(KEY_SQUARES_Y, DEFAULT_SQUARES_Y)
    fun getSquareLength(): Double = prefs.getFloat(KEY_SQUARE_LENGTH, DEFAULT_SQUARE_LENGTH.toFloat()).toDouble()
    fun getMarkerLength(): Double = prefs.getFloat(KEY_MARKER_LENGTH, DEFAULT_MARKER_LENGTH.toFloat()).toDouble()

    // Camera Configuration
    fun getCameraWidth(): Int = prefs.getInt(KEY_CAMERA_WIDTH, DEFAULT_CAMERA_WIDTH)
    fun getCameraHeight(): Int = prefs.getInt(KEY_CAMERA_HEIGHT, DEFAULT_CAMERA_HEIGHT)
    fun getCameraFps(): Int = prefs.getInt(KEY_CAMERA_FPS, DEFAULT_CAMERA_FPS)

    // Tracking Configuration
    fun getTrackingFps(): Int = prefs.getInt(KEY_TRACKING_FPS, DEFAULT_TRACKING_FPS)
    fun getMinCalibrationFrames(): Int = prefs.getInt(KEY_MIN_CALIBRATION_FRAMES, DEFAULT_MIN_CALIBRATION_FRAMES)

    /**
     * Save configuration values
     */
    fun saveConfig(key: String, value: Any) {
        prefs.edit().apply {
            when (value) {
                is Int -> putInt(key, value)
                is Float -> putFloat(key, value)
                is String -> putString(key, value)
                is Boolean -> putBoolean(key, value)
            }
            apply()
        }
    }
}
