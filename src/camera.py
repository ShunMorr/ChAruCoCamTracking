"""Threaded camera capture for real-time frame acquisition"""
import cv2
import threading
import time
from typing import Optional, Tuple
import numpy as np


class ThreadedCamera:
    """
    Threaded camera capture that always provides the latest frame

    This prevents reading old frames from the camera buffer when
    processing takes longer than the camera frame interval.
    """

    def __init__(self, device_id: int = 0, width: int = 1920,
                 height: int = 1080, fps: int = 30, is_windows: bool = True):
        """
        Initialize threaded camera

        Args:
            device_id: Camera device ID
            width: Desired frame width
            height: Desired frame height
            fps: Desired frame rate
        """
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.is_windows = is_windows

        # Camera object
        self.cap: Optional[cv2.VideoCapture] = None

        # Current frame and lock
        self.frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()

        # Thread control
        self.thread: Optional[threading.Thread] = None
        self.stopped = False

        # FPS measurement
        self.capture_fps = 0.0
        self.last_fps_time = time.time()
        self.frame_count = 0

    def start(self) -> bool:
        """
        Start camera capture thread

        Returns:
            True if successful
        """
        # Open camera
        backend = cv2.CAP_MSMF if self.is_windows else cv2.CAP_V4L2
        self.cap = cv2.VideoCapture(self.device_id, backend)

        if not self.cap.isOpened():
            print(f"カメラ {self.device_id} を開けませんでした")
            return False
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Set buffer size to 1 to minimize latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Get actual settings
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        print(f"カメラ起動: {actual_width}x{actual_height} @ {actual_fps}fps")

        # Read first frame
        ret, frame = self.cap.read()
        if not ret:
            print("初期フレームの取得に失敗しました")
            self.cap.release()
            return False

        with self.frame_lock:
            self.frame = frame

        # Start capture thread
        self.stopped = False
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        print("スレッド化カメラキャプチャ開始")
        return True

    def _capture_loop(self) -> None:
        """Continuous frame capture loop (runs in separate thread)"""
        while not self.stopped:
            ret, frame = self.cap.read()

            if ret:
                # Update frame atomically
                with self.frame_lock:
                    self.frame = frame

                # Update FPS
                self.frame_count += 1
                current_time = time.time()
                elapsed = current_time - self.last_fps_time

                if elapsed > 1.0:  # Update FPS every second
                    self.capture_fps = self.frame_count / elapsed
                    self.frame_count = 0
                    self.last_fps_time = current_time
            else:
                # Failed to read, wait a bit
                time.sleep(0.001)

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read the latest frame

        Returns:
            Tuple of (success, frame)
            - success: True if frame is available
            - frame: Latest captured frame (copy)
        """
        with self.frame_lock:
            if self.frame is None:
                return False, None
            # Return a copy to prevent race conditions
            return True, self.frame.copy()

    def get_fps(self) -> float:
        """
        Get actual capture FPS

        Returns:
            Frames per second
        """
        return self.capture_fps

    def stop(self) -> None:
        """Stop camera capture thread"""
        if self.stopped:
            return

        self.stopped = True

        if self.thread is not None:
            self.thread.join(timeout=2.0)

        if self.cap is not None:
            self.cap.release()

        print("カメラキャプチャ停止")

    def __enter__(self):
        """Context manager entry"""
        if not self.start():
            raise RuntimeError("カメラの起動に失敗しました")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False


class FPSCounter:
    """Simple FPS counter for processing performance measurement"""

    def __init__(self, window_size: int = 30):
        """
        Initialize FPS counter

        Args:
            window_size: Number of frames to average over
        """
        self.window_size = window_size
        self.timestamps = []
        self.last_time = time.time()

    def update(self) -> float:
        """
        Update FPS counter with current frame

        Returns:
            Current FPS
        """
        current_time = time.time()
        self.timestamps.append(current_time)

        # Keep only recent timestamps
        if len(self.timestamps) > self.window_size:
            self.timestamps.pop(0)

        # Calculate FPS
        if len(self.timestamps) < 2:
            return 0.0

        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed == 0:
            return 0.0

        return (len(self.timestamps) - 1) / elapsed

    def reset(self) -> None:
        """Reset FPS counter"""
        self.timestamps = []
        self.last_time = time.time()
