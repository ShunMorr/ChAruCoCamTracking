"""Camera calibration using ChArUco board"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from .utils import save_yaml, load_yaml
from .camera import ThreadedCamera


class CameraCalibrator:
    """Camera calibration using ChArUco board"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize calibrator

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.charuco_config = config['charuco']

        # Setup ArUco dictionary
        aruco_dict_name = self.charuco_config['dictionary']
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(
            getattr(cv2.aruco, aruco_dict_name)
        )

        # Create ChArUco board
        self.board = cv2.aruco.CharucoBoard(
            (self.charuco_config['squares_x'], self.charuco_config['squares_y']),
            self.charuco_config['square_length'],
            self.charuco_config['marker_length'],
            self.aruco_dict
        )

        # Setup detector parameters
        self.detector_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.CharucoDetector(self.board, detectorParams=self.detector_params)

        # Storage for calibration data
        self.all_charuco_corners: List[np.ndarray] = []
        self.all_charuco_ids: List[np.ndarray] = []
        self.image_size: Optional[Tuple[int, int]] = None

    def collect_calibration_frame(self, frame: np.ndarray) -> bool:
        """
        Collect a frame for calibration

        Args:
            frame: Input image

        Returns:
            True if frame was successfully collected
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.image_size = gray.shape[::-1]

        # Detect ChArUco board
        charuco_corners, charuco_ids, marker_corners, marker_ids = self.detector.detectBoard(gray)

        if charuco_corners is not None and len(charuco_corners) > 3:
            self.all_charuco_corners.append(charuco_corners)
            self.all_charuco_ids.append(charuco_ids)
            return True

        return False

    def calibrate(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Perform camera calibration

        Returns:
            Tuple of (success, calibration_params)
        """
        if len(self.all_charuco_corners) < self.config['calibration']['min_frames']:
            print(f"キャリブレーションには最低{self.config['calibration']['min_frames']}フレーム必要です")
            print(f"現在のフレーム数: {len(self.all_charuco_corners)}")
            return False, None

        # Perform calibration
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
            self.all_charuco_corners,
            self.all_charuco_ids,
            self.board,
            self.image_size,
            None,
            None
        )

        if not ret:
            print("キャリブレーションに失敗しました")
            return False, None

        # Calculate reprojection error
        total_error = 0
        total_points = 0
        for i in range(len(self.all_charuco_corners)):
            # Project points
            img_points2, _ = cv2.projectPoints(
                self.board.getChessboardCorners()[self.all_charuco_ids[i].flatten()],
                rvecs[i],
                tvecs[i],
                camera_matrix,
                dist_coeffs
            )
            error = cv2.norm(self.all_charuco_corners[i], img_points2, cv2.NORM_L2) / len(img_points2)
            total_error += error
            total_points += 1

        mean_error = total_error / total_points

        calibration_params = {
            'camera_matrix': camera_matrix,
            'dist_coeffs': dist_coeffs,
            'image_size': list(self.image_size),
            'reprojection_error': float(mean_error),
            'num_frames': len(self.all_charuco_corners),
        }

        print(f"キャリブレーション成功!")
        print(f"使用フレーム数: {len(self.all_charuco_corners)}")
        print(f"再投影誤差: {mean_error:.4f} pixels")

        return True, calibration_params

    def save_calibration(self, calibration_params: Dict[str, Any], filepath: str) -> None:
        """
        Save calibration parameters to file

        Args:
            calibration_params: Calibration parameters
            filepath: Output file path
        """
        save_yaml(calibration_params, filepath)

    @staticmethod
    def load_calibration(filepath: str) -> Dict[str, Any]:
        """
        Load calibration parameters from file

        Args:
            filepath: Input file path

        Returns:
            Calibration parameters
        """
        params = load_yaml(filepath)

        # Convert lists back to numpy arrays
        if 'camera_matrix' in params:
            params['camera_matrix'] = np.array(params['camera_matrix'])
        if 'dist_coeffs' in params:
            params['dist_coeffs'] = np.array(params['dist_coeffs'])

        return params

    def reset(self) -> None:
        """Reset collected calibration data"""
        self.all_charuco_corners = []
        self.all_charuco_ids = []
        self.image_size = None


def run_calibration_interactive(config: Dict[str, Any]) -> Optional[str]:
    """
    Run interactive camera calibration

    Args:
        config: Configuration dictionary

    Returns:
        Path to saved calibration file or None if failed
    """
    calibrator = CameraCalibrator(config)

    # Initialize threaded camera
    camera = ThreadedCamera(
        device_id=config['camera']['device_id'],
        width=config['camera']['width'],
        height=config['camera']['height'],
        fps=config['camera']['fps']
    )

    if not camera.start():
        print("カメラを開けませんでした")
        return None

    print("=== カメラキャリブレーション ===")
    print(f"目標フレーム数: {config['calibration']['min_frames']}")
    print("ChArUcoボードを様々な角度・位置で映してください")
    print("[SPACE]: フレーム取得, [C]: キャリブレーション実行, [Q]: 終了")

    collected_frames = 0

    try:
        while True:
            # Get latest frame from camera thread
            ret, frame = camera.read()
            if not ret:
                print("フレーム取得に失敗しました")
                break

            display_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect ChArUco board for visualization
            charuco_corners, charuco_ids, marker_corners, marker_ids = calibrator.detector.detectBoard(gray)

            if charuco_corners is not None and len(charuco_corners) > 0:
                cv2.aruco.drawDetectedCornersCharuco(display_frame, charuco_corners, charuco_ids)

            # Display info
            cv2.putText(display_frame, f"Frames: {collected_frames}/{config['calibration']['min_frames']}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Calibration', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("キャリブレーションを中止しました")
                break
            elif key == ord(' '):
                if calibrator.collect_calibration_frame(frame):
                    collected_frames += 1
                    print(f"フレーム取得成功 ({collected_frames}/{config['calibration']['min_frames']})")
                else:
                    print("ChArUcoボードが検出できませんでした")
            elif key == ord('c'):
                success, calib_params = calibrator.calibrate()
                if success:
                    save_path = config['calibration']['save_path']
                    calibrator.save_calibration(calib_params, save_path)
                    camera.stop()
                    cv2.destroyAllWindows()
                    return save_path

    finally:
        camera.stop()
        cv2.destroyAllWindows()

    return None
