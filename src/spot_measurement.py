"""Spot measurement of camera position"""
import cv2
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
from .charuco_detector import CharucoDetector
from .utils import save_yaml, format_pose


class SpotMeasurement:
    """Measure camera position at a specific spot"""

    def __init__(self, config: Dict[str, Any], calibration_params: Dict[str, Any]):
        """
        Initialize spot measurement

        Args:
            config: Configuration dictionary
            calibration_params: Camera calibration parameters
        """
        self.config = config
        self.detector = CharucoDetector(config, calibration_params)

        self.measurements: List[Dict[str, Any]] = []

    def measure_pose(self, frame: np.ndarray, num_samples: int = 30) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Measure pose by averaging multiple samples

        Args:
            frame: Current camera frame
            num_samples: Number of samples to average

        Returns:
            Tuple of (success, pose_data)
        """
        print(f"測定中... ({num_samples}サンプル)")

        # Collect multiple samples
        rvecs = []
        tvecs = []
        qualities = []

        for i in range(num_samples):
            success, rvec, tvec, corners, ids = self.detector.detect_and_estimate_pose(frame)

            if success:
                rvecs.append(rvec)
                tvecs.append(tvec)
                quality = self.detector.get_pose_quality_score(corners, ids)
                qualities.append(quality)

        if len(rvecs) == 0:
            print("測定に失敗しました（ボードが検出できません）")
            return False, None

        # Average the measurements
        avg_rvec = np.mean(rvecs, axis=0)
        avg_tvec = np.mean(tvecs, axis=0)
        avg_quality = np.mean(qualities)

        # Calculate standard deviation
        std_tvec = np.std(tvecs, axis=0)

        # Format pose
        pose = format_pose(avg_tvec, avg_rvec)
        pose['quality'] = float(avg_quality)
        pose['num_samples'] = len(rvecs)
        pose['std_dev'] = {
            'x_mm': float(std_tvec[0, 0] * 1000),
            'y_mm': float(std_tvec[1, 0] * 1000),
            'z_mm': float(std_tvec[2, 0] * 1000),
        }

        print(f"測定完了: {len(rvecs)}/{num_samples} サンプル使用")
        print(f"位置: X={pose['translation']['x']:.3f}mm, Y={pose['translation']['y']:.3f}mm")
        print(f"標準偏差: X={pose['std_dev']['x_mm']:.4f}mm, Y={pose['std_dev']['y_mm']:.4f}mm")

        return True, pose

    def save_measurement(self, pose: Dict[str, Any], filepath: str) -> None:
        """
        Save measurement to YAML file

        Args:
            pose: Pose data
            filepath: Output file path
        """
        data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'measurement_type': 'spot',
            },
            'pose': pose,
        }

        save_yaml(data, filepath)
        print(f"測定結果を保存しました: {filepath}")


def run_spot_measurement(config: Dict[str, Any], calibration_params: Dict[str, Any],
                         output_file: str, num_samples: int = 30) -> Optional[str]:
    """
    Run spot measurement

    Args:
        config: Configuration dictionary
        calibration_params: Camera calibration parameters
        output_file: Output file path
        num_samples: Number of samples to average

    Returns:
        Output file path if successful, None otherwise
    """
    measurement = SpotMeasurement(config, calibration_params)

    # Open camera
    cap = cv2.VideoCapture(config['camera']['device_id'])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['camera']['width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['camera']['height'])
    cap.set(cv2.CAP_PROP_FPS, config['camera']['fps'])

    if not cap.isOpened():
        print("カメラを開けませんでした")
        return None

    print("=== スポット測定 ===")
    print(f"サンプル数: {num_samples}")
    print("[SPACE]: 測定実行, [Q]: 終了")

    measured = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレーム取得に失敗しました")
            break

        # Try to detect and estimate pose
        success, rvec, tvec, corners, ids = measurement.detector.detect_and_estimate_pose(frame)

        display_frame = frame.copy()

        if success:
            # Draw detection
            display_frame = measurement.detector.draw_detection(display_frame, corners, ids, rvec, tvec)

            # Get quality
            quality = measurement.detector.get_pose_quality_score(corners, ids)
            cv2.putText(display_frame, f"Quality: {quality:.2f}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Display instructions
        cv2.putText(display_frame, "Press SPACE to measure",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow('Spot Measurement', display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            if not measured:
                print("測定を中止しました")
            break
        elif key == ord(' '):
            # Collect samples for measurement
            samples_rvecs = []
            samples_tvecs = []
            samples_qualities = []

            print(f"測定中... ({num_samples}サンプル)")

            for i in range(num_samples):
                ret, frame = cap.read()
                if not ret:
                    continue

                success, rvec, tvec, corners, ids = measurement.detector.detect_and_estimate_pose(frame)

                if success:
                    samples_rvecs.append(rvec)
                    samples_tvecs.append(tvec)
                    quality = measurement.detector.get_pose_quality_score(corners, ids)
                    samples_qualities.append(quality)

                    # Visual feedback
                    display_frame = frame.copy()
                    display_frame = measurement.detector.draw_detection(display_frame, corners, ids, rvec, tvec)
                    cv2.putText(display_frame, f"Sampling: {len(samples_rvecs)}/{num_samples}",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    cv2.imshow('Spot Measurement', display_frame)
                    cv2.waitKey(1)

            if len(samples_rvecs) > 0:
                # Average measurements
                avg_rvec = np.mean(samples_rvecs, axis=0)
                avg_tvec = np.mean(samples_tvecs, axis=0)
                avg_quality = np.mean(samples_qualities)
                std_tvec = np.std(samples_tvecs, axis=0)

                # Format pose
                pose = format_pose(avg_tvec, avg_rvec)
                pose['quality'] = float(avg_quality)
                pose['num_samples'] = len(samples_rvecs)
                pose['std_dev'] = {
                    'x_mm': float(std_tvec[0, 0] * 1000),
                    'y_mm': float(std_tvec[1, 0] * 1000),
                    'z_mm': float(std_tvec[2, 0] * 1000),
                }

                print(f"測定完了: {len(samples_rvecs)}/{num_samples} サンプル使用")
                print(f"位置: X={pose['translation']['x']:.3f}mm, Y={pose['translation']['y']:.3f}mm")
                print(f"標準偏差: X={pose['std_dev']['x_mm']:.4f}mm, Y={pose['std_dev']['y_mm']:.4f}mm")

                # Save measurement
                measurement.save_measurement(pose, output_file)
                measured = True

                # Wait a bit to show result
                cv2.waitKey(1000)
                break
            else:
                print("測定に失敗しました（ボードが検出できません）")

    cap.release()
    cv2.destroyAllWindows()

    return output_file if measured else None
