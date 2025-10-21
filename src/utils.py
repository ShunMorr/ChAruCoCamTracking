"""Utility functions for YAML I/O and coordinate transformations"""
import yaml
import numpy as np
from typing import Dict, List, Any, Tuple
from pathlib import Path


def save_yaml(data: Dict[str, Any], filepath: str) -> None:
    """
    Save data to YAML file

    Args:
        data: Dictionary to save
        filepath: Output file path
    """
    # Convert numpy arrays to lists for YAML serialization
    yaml_data = _convert_numpy_to_list(data)

    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
    print(f"データを保存しました: {filepath}")


def load_yaml(filepath: str) -> Dict[str, Any]:
    """
    Load data from YAML file

    Args:
        filepath: Input file path

    Returns:
        Loaded dictionary
    """
    if not Path(filepath).exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data


def _convert_numpy_to_list(obj: Any) -> Any:
    """
    Recursively convert numpy arrays to lists for YAML serialization

    Args:
        obj: Object to convert

    Returns:
        Converted object
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: _convert_numpy_to_list(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_to_list(item) for item in obj]
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    else:
        return obj


def rotation_matrix_to_euler_angles(R: np.ndarray) -> Tuple[float, float, float]:
    """
    Convert rotation matrix to Euler angles (roll, pitch, yaw)
    Uses ZYX convention

    Args:
        R: 3x3 rotation matrix

    Returns:
        Tuple of (roll, pitch, yaw) in radians
    """
    sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)

    singular = sy < 1e-6

    if not singular:
        roll = np.arctan2(R[2, 1], R[2, 2])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        roll = np.arctan2(-R[1, 2], R[1, 1])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = 0

    return roll, pitch, yaw


def rodrigues_to_euler_angles(rvec: np.ndarray) -> Tuple[float, float, float]:
    """
    Convert Rodrigues vector to Euler angles

    Args:
        rvec: Rodrigues rotation vector (3,1) or (1,3)

    Returns:
        Tuple of (roll, pitch, yaw) in radians
    """
    import cv2
    R, _ = cv2.Rodrigues(rvec)
    return rotation_matrix_to_euler_angles(R)


def format_pose(tvec: np.ndarray, rvec: np.ndarray) -> Dict[str, Any]:
    """
    Format pose data for output

    Args:
        tvec: Translation vector (x, y, z) in meters
        rvec: Rodrigues rotation vector

    Returns:
        Dictionary with formatted pose data
    """
    roll, pitch, yaw = rodrigues_to_euler_angles(rvec)

    return {
        'translation': {
            'x': float(tvec[0, 0] * 1000),  # Convert to mm
            'y': float(tvec[1, 0] * 1000),  # Convert to mm
            'z': float(tvec[2, 0] * 1000),  # Convert to mm
        },
        'rotation': {
            'roll': float(np.degrees(roll)),
            'pitch': float(np.degrees(pitch)),
            'yaw': float(np.degrees(yaw)),
        }
    }


def calculate_displacement(pose1: Dict[str, Any], pose2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate displacement between two poses

    Args:
        pose1: First pose
        pose2: Second pose

    Returns:
        Displacement in x, y, yaw
    """
    dx = pose2['translation']['x'] - pose1['translation']['x']
    dy = pose2['translation']['y'] - pose1['translation']['y']
    dz = pose2['translation']['z'] - pose1['translation']['z']

    dyaw = pose2['rotation']['yaw'] - pose1['rotation']['yaw']

    # Normalize yaw to [-180, 180]
    while dyaw > 180:
        dyaw -= 360
    while dyaw < -180:
        dyaw += 360

    return {
        'displacement': {
            'x_mm': float(dx),
            'y_mm': float(dy),
            'z_mm': float(dz),
            'yaw_deg': float(dyaw),
        },
        'distance_2d_mm': float(np.sqrt(dx**2 + dy**2)),
        'distance_3d_mm': float(np.sqrt(dx**2 + dy**2 + dz**2)),
    }
