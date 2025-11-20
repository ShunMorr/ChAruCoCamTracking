# Add project specific ProGuard rules here.

# OpenCV
-keep class org.opencv.** { *; }

# SnakeYAML
-keep class org.yaml.snakeyaml.** { *; }

# Keep data classes
-keep class com.charuco.tracking.utils.** { *; }
