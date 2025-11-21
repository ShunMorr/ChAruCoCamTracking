"""Continuous trajectory tracking"""
import cv2
import numpy as np
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .charuco_detector import CharucoDetector
from .utils import save_yaml, format_pose, calculate_displacement
from .camera import ThreadedCamera, FPSCounter


class TrajectoryTracker:
    """Track camera trajectory continuously"""

    def __init__(self, config: Dict[str, Any], calibration_params: Dict[str, Any]):
        """
        Initialize tracker

        Args:
            config: Configuration dictionary
            calibration_params: Camera calibration parameters
        """
        self.config = config
        self.detector = CharucoDetector(config, calibration_params)

        self.trajectory: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.is_tracking = False

        # Tracking FPS control
        self.tracking_fps = config.get('tracking', {}).get('tracking_fps', 30)
        self.tracking_interval = 1.0 / self.tracking_fps if self.tracking_fps > 0 else 0
        self.last_tracking_time = 0.0

        # Tracking rate measurement
        self.tracking_rate_counter = FPSCounter(window_size=30)

    def start_tracking(self) -> None:
        """Start trajectory tracking"""
        self.trajectory = []
        self.start_time = cv2.getTickCount() / cv2.getTickFrequency()
        self.last_tracking_time = self.start_time
        self.tracking_rate_counter.reset()
        self.is_tracking = True
        print("トラッキング開始")

    def stop_tracking(self) -> None:
        """Stop trajectory tracking"""
        self.is_tracking = False
        print("トラッキング停止")

    def add_pose(self, current_time: float,
                 rvec: np.ndarray, tvec: np.ndarray,
                 corners: np.ndarray, ids: np.ndarray) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Add current pose to trajectory (with FPS control)

        Args:
            current_time: Current timestamp
            rvec: Rotation vector from detection
            tvec: Translation vector from detection
            corners: Detected corners
            ids: Detected marker IDs

        Returns:
            Tuple of (success, pose_data)
        """
        if not self.is_tracking:
            return False, None

        # Check if enough time has passed since last tracking
        if current_time - self.last_tracking_time < self.tracking_interval:
            return False, None  # Skip this frame

        # Update last tracking time
        self.last_tracking_time = current_time

        # Get current timestamp relative to start
        elapsed_time = current_time - self.start_time

        # Get quality score
        quality = self.detector.get_pose_quality_score(corners, ids)

        # Format pose
        pose = format_pose(tvec, rvec)
        pose['timestamp'] = float(elapsed_time)
        pose['quality'] = float(quality)
        pose['num_corners'] = int(len(corners)) if corners is not None else 0

        self.trajectory.append(pose)

        # Update tracking rate counter
        self.tracking_rate_counter.update()

        return True, pose

    def get_total_displacement(self) -> Optional[Dict[str, Any]]:
        """
        Calculate total displacement from start to end

        Returns:
            Displacement data or None if trajectory is empty
        """
        if len(self.trajectory) < 2:
            return None

        start_pose = self.trajectory[0]
        end_pose = self.trajectory[-1]

        displacement = calculate_displacement(start_pose, end_pose)
        displacement['duration_sec'] = end_pose['timestamp'] - start_pose['timestamp']

        return displacement

    def save_trajectory(self, filepath: str) -> None:
        """
        Save trajectory to YAML file

        Args:
            filepath: Output file path
        """
        total_displacement = self.get_total_displacement()

        data = {
            'metadata': {
                'num_poses': len(self.trajectory),
                'duration_sec': self.trajectory[-1]['timestamp'] if self.trajectory else 0,
                'timestamp': datetime.now().isoformat(),
            },
            'trajectory': self.trajectory,
            'total_displacement': total_displacement,
        }

        save_yaml(data, filepath)
        print(f"軌跡データを保存しました: {filepath}")

        if total_displacement:
            print(f"総移動距離 (2D): {total_displacement['distance_2d_mm']:.3f} mm")
            print(f"X方向移動: {total_displacement['displacement']['x_mm']:.3f} mm")
            print(f"Y方向移動: {total_displacement['displacement']['y_mm']:.3f} mm")
            print(f"Yaw回転: {total_displacement['displacement']['yaw_deg']:.3f} deg")


def run_trajectory_tracking(config: Dict[str, Any], calibration_params: Dict[str, Any],
                            output_file: str) -> Optional[str]:
    """
    Run continuous trajectory tracking

    Args:
        config: Configuration dictionary
        calibration_params: Camera calibration parameters
        output_file: Output file path

    Returns:
        Output file path if successful, None otherwise
    """
    tracker = TrajectoryTracker(config, calibration_params)

    # Display (headless) setting
    display_enabled = config.get('display', {}).get('enabled', True)

    # Initialize threaded camera
    camera = ThreadedCamera(
        device_id=config['camera']['device_id'],
        width=config['camera']['width'],
        height=config['camera']['height'],
        fps=config['camera']['fps'],
        is_windows=config['camera'].get('is_windows', True)
    )

    if not camera.start():
        print("カメラを開けませんでした")
        return None

    # Last detected pose for display
    last_pose_display = None
    last_detection_time = 0.0

    print("=== 連続トラッキング ===")
    print("[S]: トラッキング開始, [E]: トラッキング終了・保存, [Q]: 終了")

    try:
        while True:
            # Get latest frame from camera thread
            ret, frame = camera.read()
            if not ret:
                print("フレーム取得に失敗しました")
                break

            # Get current time for tracking FPS control
            current_time = cv2.getTickCount() / cv2.getTickFrequency()

            display_frame = frame.copy()

            # Check if enough time has passed to perform detection
            should_detect = (current_time - last_detection_time >= tracker.tracking_interval)

            if should_detect:
                # Perform pose detection and estimation
                success, rvec, tvec, corners, ids = tracker.detector.detect_and_estimate_pose(frame)
                last_detection_time = current_time

                if success:
                    # Draw detection
                    display_frame = tracker.detector.draw_detection(display_frame, corners, ids, rvec, tvec)

                    # Calculate pose for display
                    from .utils import format_pose
                    last_pose_display = format_pose(tvec, rvec)

                    # Add pose to trajectory if tracking
                    if tracker.is_tracking:
                        tracker.add_pose(current_time, rvec, tvec, corners, ids)
                else:
                    # Detection failed, clear display
                    last_pose_display = None

            # Display last known pose (if available)
            if last_pose_display is not None:
                text = f"X:{last_pose_display['translation']['x']:.1f} Y:{last_pose_display['translation']['y']:.1f} Yaw:{last_pose_display['rotation']['yaw']:.1f}"
                cv2.putText(display_frame, text, (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Display tracking status
            status_text = "TRACKING" if tracker.is_tracking else "STOPPED"
            status_color = (0, 255, 0) if tracker.is_tracking else (0, 0, 255)
            cv2.putText(display_frame, status_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

            # Display number of poses
            if tracker.is_tracking:
                cv2.putText(display_frame, f"Poses: {len(tracker.trajectory)}",
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Update and display FPS
            capture_fps = camera.get_fps()
            actual_tracking_fps = tracker.tracking_rate_counter.update() if tracker.is_tracking else 0.0
            fps_text = f"Capture: {capture_fps:.1f} fps | Tracking: {actual_tracking_fps:.1f}/{tracker.tracking_fps} fps"
            cv2.putText(display_frame, fps_text, (10, display_frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            if display_enabled:
                cv2.imshow('Trajectory Tracking', display_frame)
                # Window close (X) -> stop session
                if cv2.getWindowProperty('Trajectory Tracking', cv2.WND_PROP_VISIBLE) < 1:
                    print("\nウィンドウが閉じられたためセッションを終了します")
                    break

            key = (cv2.waitKey(1) & 0xFF) if display_enabled else -1

            if key == ord('q'):
                print("\nトラッキングを中止しました")
                break
            elif key == ord('s'):
                if not tracker.is_tracking:
                    tracker.start_tracking()
            elif key == ord('e'):
                if tracker.is_tracking:
                    tracker.stop_tracking()
                    if len(tracker.trajectory) > 0:
                        print()  # New line after real-time output
                        tracker.save_trajectory(output_file)
                        camera.stop()
                        cv2.destroyAllWindows()
                        return output_file
                    else:
                        print("\n軌跡データがありません")

    finally:
        camera.stop()
        cv2.destroyAllWindows()

    return None
