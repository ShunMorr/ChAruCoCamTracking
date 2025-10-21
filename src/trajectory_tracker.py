"""Continuous trajectory tracking"""
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from .charuco_detector import CharucoDetector
from .utils import save_yaml, format_pose, calculate_displacement


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

    def start_tracking(self) -> None:
        """Start trajectory tracking"""
        self.trajectory = []
        self.start_time = cv2.getTickCount() / cv2.getTickFrequency()
        self.is_tracking = True
        print("トラッキング開始")

    def stop_tracking(self) -> None:
        """Stop trajectory tracking"""
        self.is_tracking = False
        print("トラッキング停止")

    def add_pose(self, frame: np.ndarray) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Add current pose to trajectory

        Args:
            frame: Current camera frame

        Returns:
            Tuple of (success, pose_data)
        """
        if not self.is_tracking:
            return False, None

        success, rvec, tvec, corners, ids = self.detector.detect_and_estimate_pose(frame)

        if not success:
            return False, None

        # Get current timestamp
        current_time = cv2.getTickCount() / cv2.getTickFrequency()
        elapsed_time = current_time - self.start_time

        # Get quality score
        quality = self.detector.get_pose_quality_score(corners, ids)

        # Format pose
        pose = format_pose(tvec, rvec)
        pose['timestamp'] = float(elapsed_time)
        pose['quality'] = float(quality)
        pose['num_corners'] = int(len(corners)) if corners is not None else 0

        self.trajectory.append(pose)

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

    # Open camera
    cap = cv2.VideoCapture(config['camera']['device_id'])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['camera']['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['camera']['height'])
    cap.set(cv2.CAP_PROP_FPS, config['camera']['fps'])

    if not cap.isOpened():
        print("カメラを開けませんでした")
        return None

    print("=== 連続トラッキング ===")
    print("[S]: トラッキング開始, [E]: トラッキング終了・保存, [Q]: 終了")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレーム取得に失敗しました")
            break

        # Try to detect and estimate pose
        success, rvec, tvec, corners, ids = tracker.detector.detect_and_estimate_pose(frame)

        display_frame = frame.copy()

        if success:
            # Draw detection
            display_frame = tracker.detector.draw_detection(display_frame, corners, ids, rvec, tvec)

            # Add pose to trajectory if tracking
            if tracker.is_tracking:
                pose_success, pose = tracker.add_pose(frame)
                if pose_success:
                    # Display current pose
                    text = f"X:{pose['translation']['x']:.1f} Y:{pose['translation']['y']:.1f} Yaw:{pose['rotation']['yaw']:.1f}"
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

        cv2.imshow('Trajectory Tracking', display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("トラッキングを中止しました")
            break
        elif key == ord('s'):
            if not tracker.is_tracking:
                tracker.start_tracking()
        elif key == ord('e'):
            if tracker.is_tracking:
                tracker.stop_tracking()
                if len(tracker.trajectory) > 0:
                    tracker.save_trajectory(output_file)
                    cap.release()
                    cv2.destroyAllWindows()
                    return output_file
                else:
                    print("軌跡データがありません")

    cap.release()
    cv2.destroyAllWindows()
    return None
