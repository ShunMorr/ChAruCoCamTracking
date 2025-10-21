"""Compare positions and calculate displacement"""
from typing import Dict, Any
from datetime import datetime
from .utils import load_yaml, save_yaml, calculate_displacement


def compare_spot_measurements(file1: str, file2: str, output_file: str) -> bool:
    """
    Compare two spot measurements and calculate displacement

    Args:
        file1: First measurement file
        file2: Second measurement file
        output_file: Output file for comparison result

    Returns:
        True if successful
    """
    try:
        # Load measurements
        print(f"測定1を読み込み: {file1}")
        data1 = load_yaml(file1)
        pose1 = data1['pose']

        print(f"測定2を読み込み: {file2}")
        data2 = load_yaml(file2)
        pose2 = data2['pose']

        # Calculate displacement
        displacement = calculate_displacement(pose1, pose2)

        # Create comparison result
        result = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'comparison_type': 'spot_to_spot',
                'file1': file1,
                'file2': file2,
            },
            'pose1': {
                'file': file1,
                'timestamp': data1['metadata']['timestamp'],
                'position': pose1,
            },
            'pose2': {
                'file': file2,
                'timestamp': data2['metadata']['timestamp'],
                'position': pose2,
            },
            'displacement': displacement,
        }

        # Save result
        save_yaml(result, output_file)

        # Print summary
        print("\n=== 位置比較結果 ===")
        print(f"測定1: X={pose1['translation']['x']:.3f}mm, Y={pose1['translation']['y']:.3f}mm, Yaw={pose1['rotation']['yaw']:.3f}deg")
        print(f"測定2: X={pose2['translation']['x']:.3f}mm, Y={pose2['translation']['y']:.3f}mm, Yaw={pose2['rotation']['yaw']:.3f}deg")
        print(f"\n移動量:")
        print(f"  X方向: {displacement['displacement']['x_mm']:.3f} mm")
        print(f"  Y方向: {displacement['displacement']['y_mm']:.3f} mm")
        print(f"  Z方向: {displacement['displacement']['z_mm']:.3f} mm")
        print(f"  Yaw回転: {displacement['displacement']['yaw_deg']:.3f} deg")
        print(f"  2D距離: {displacement['distance_2d_mm']:.3f} mm")
        print(f"  3D距離: {displacement['distance_3d_mm']:.3f} mm")

        # Calculate and display uncertainty
        if 'std_dev' in pose1 and 'std_dev' in pose2:
            # Combined standard deviation (root sum of squares)
            import numpy as np
            std_combined_x = np.sqrt(pose1['std_dev']['x_mm']**2 + pose2['std_dev']['x_mm']**2)
            std_combined_y = np.sqrt(pose1['std_dev']['y_mm']**2 + pose2['std_dev']['y_mm']**2)

            print(f"\n測定不確かさ（2σ）:")
            print(f"  X方向: ±{2 * std_combined_x:.4f} mm")
            print(f"  Y方向: ±{2 * std_combined_y:.4f} mm")

        print(f"\n結果を保存しました: {output_file}")

        return True

    except Exception as e:
        print(f"エラー: {e}")
        return False


def compare_trajectory_endpoints(trajectory_file: str, output_file: str) -> bool:
    """
    Compare start and end points of a trajectory

    Args:
        trajectory_file: Trajectory file
        output_file: Output file for comparison result

    Returns:
        True if successful
    """
    try:
        # Load trajectory
        print(f"軌跡データを読み込み: {trajectory_file}")
        data = load_yaml(trajectory_file)

        if 'trajectory' not in data or len(data['trajectory']) < 2:
            print("エラー: 軌跡データが不足しています")
            return False

        # Get start and end poses
        start_pose = data['trajectory'][0]
        end_pose = data['trajectory'][-1]

        # Calculate displacement
        displacement = calculate_displacement(start_pose, end_pose)

        # Create comparison result
        result = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'comparison_type': 'trajectory_endpoints',
                'trajectory_file': trajectory_file,
                'num_poses': len(data['trajectory']),
                'duration_sec': data['metadata']['duration_sec'],
            },
            'start_pose': start_pose,
            'end_pose': end_pose,
            'displacement': displacement,
        }

        # Save result
        save_yaml(result, output_file)

        # Print summary
        print("\n=== 軌跡端点比較結果 ===")
        print(f"軌跡ポーズ数: {len(data['trajectory'])}")
        print(f"継続時間: {data['metadata']['duration_sec']:.2f} 秒")
        print(f"\n開始位置: X={start_pose['translation']['x']:.3f}mm, Y={start_pose['translation']['y']:.3f}mm, Yaw={start_pose['rotation']['yaw']:.3f}deg")
        print(f"終了位置: X={end_pose['translation']['x']:.3f}mm, Y={end_pose['translation']['y']:.3f}mm, Yaw={end_pose['rotation']['yaw']:.3f}deg")
        print(f"\n総移動量:")
        print(f"  X方向: {displacement['displacement']['x_mm']:.3f} mm")
        print(f"  Y方向: {displacement['displacement']['y_mm']:.3f} mm")
        print(f"  Z方向: {displacement['displacement']['z_mm']:.3f} mm")
        print(f"  Yaw回転: {displacement['displacement']['yaw_deg']:.3f} deg")
        print(f"  2D距離: {displacement['distance_2d_mm']:.3f} mm")
        print(f"  3D距離: {displacement['distance_3d_mm']:.3f} mm")

        print(f"\n結果を保存しました: {output_file}")

        return True

    except Exception as e:
        print(f"エラー: {e}")
        return False
