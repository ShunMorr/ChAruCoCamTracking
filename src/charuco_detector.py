"""ChArUco board detection and pose estimation"""
import cv2
import numpy as np
from typing import Dict, Optional, Tuple, Any


class CharucoDetector:
    """Detect ChArUco board and estimate pose"""

    def __init__(self, config: Dict[str, Any], calibration_params: Dict[str, Any]):
        """
        Initialize detector

        Args:
            config: Configuration dictionary
            calibration_params: Camera calibration parameters
        """
        self.config = config
        self.charuco_config = config['charuco']

        # Camera calibration parameters
        self.camera_matrix = calibration_params['camera_matrix']
        self.dist_coeffs = calibration_params['dist_coeffs']

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
        # Fine-tune detector parameters for better precision
        self.detector_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector_params.cornerRefinementWinSize = 5
        self.detector_params.cornerRefinementMaxIterations = 30
        self.detector_params.cornerRefinementMinAccuracy = 0.01

        self.detector = cv2.aruco.CharucoDetector(self.board, detectorParams=self.detector_params)

    def detect_and_estimate_pose(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Detect ChArUco board and estimate camera pose

        Args:
            frame: Input image (BGR)

        Returns:
            Tuple of (success, rvec, tvec, charuco_corners, charuco_ids)
            - success: True if pose estimation was successful
            - rvec: Rotation vector (Rodrigues)
            - tvec: Translation vector (x, y, z) in meters
            - charuco_corners: Detected charuco corner coordinates
            - charuco_ids: IDs of detected charuco corners
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect ChArUco board
        charuco_corners, charuco_ids, marker_corners, marker_ids = self.detector.detectBoard(gray)

        if charuco_corners is None or len(charuco_corners) < 4:
            return False, None, None, None, None

        # Estimate pose
        success, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(
            charuco_corners,
            charuco_ids,
            self.board,
            self.camera_matrix,
            self.dist_coeffs,
            None,
            None
        )

        if not success:
            return False, None, None, None, None

        return True, rvec, tvec, charuco_corners, charuco_ids

    def draw_detection(self, frame: np.ndarray, charuco_corners: np.ndarray,
                       charuco_ids: np.ndarray, rvec: np.ndarray,
                       tvec: np.ndarray) -> np.ndarray:
        """
        Draw detected board and pose on frame

        Args:
            frame: Input image
            charuco_corners: Detected charuco corners
            charuco_ids: Charuco corner IDs
            rvec: Rotation vector
            tvec: Translation vector

        Returns:
            Frame with drawn detection
        """
        display_frame = frame.copy()

        # Draw detected corners
        if charuco_corners is not None and len(charuco_corners) > 0:
            cv2.aruco.drawDetectedCornersCharuco(display_frame, charuco_corners, charuco_ids)

        # Draw coordinate axes
        if rvec is not None and tvec is not None:
            axis_length = self.charuco_config['square_length'] * 2
            cv2.drawFrameAxes(
                display_frame,
                self.camera_matrix,
                self.dist_coeffs,
                rvec,
                tvec,
                axis_length,
                3
            )

        return display_frame

    def get_pose_quality_score(self, charuco_corners: np.ndarray,
                               charuco_ids: np.ndarray) -> float:
        """
        Calculate pose quality score based on number of detected corners

        Args:
            charuco_corners: Detected charuco corners
            charuco_ids: Charuco corner IDs

        Returns:
            Quality score (0-1)
        """
        if charuco_corners is None:
            return 0.0

        # Total possible corners
        total_corners = (self.charuco_config['squares_x'] - 1) * (self.charuco_config['squares_y'] - 1)
        detected_corners = len(charuco_corners)

        return min(detected_corners / total_corners, 1.0)
