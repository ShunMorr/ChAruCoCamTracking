#!/usr/bin/env python3
"""3D trajectory visualization tool using Plotly"""
import argparse
import sys
import yaml
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Tuple


def load_trajectory(filepath: str) -> Dict[str, Any]:
    """
    Load trajectory data from YAML file

    Args:
        filepath: Path to trajectory YAML file

    Returns:
        Trajectory data dictionary
    """
    try:
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        if 'trajectory' not in data:
            raise ValueError("Invalid trajectory file: 'trajectory' key not found")

        return data
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {filepath}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"エラー: YAMLの読み込みに失敗しました: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


def rotation_matrix_from_euler(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """
    Create rotation matrix from Euler angles (in degrees)

    Args:
        roll: Roll angle in degrees
        pitch: Pitch angle in degrees
        yaw: Yaw angle in degrees

    Returns:
        3x3 rotation matrix
    """
    # Convert to radians
    roll = np.deg2rad(roll)
    pitch = np.deg2rad(pitch)
    yaw = np.deg2rad(yaw)

    # Rotation matrices for each axis
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])

    R_y = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    R_z = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    # Combined rotation: R = Rz * Ry * Rx
    R = R_z @ R_y @ R_x

    return R


def create_arrow_trace(start: np.ndarray, direction: np.ndarray,
                       color: str, name: str,
                       showlegend: bool = True) -> Tuple[go.Scatter3d, go.Cone]:
    """
    Create arrow traces for 3D plot

    Args:
        start: Starting position [x, y, z]
        direction: Direction vector [dx, dy, dz]
        color: Arrow color
        name: Trace name for legend
        showlegend: Show in legend

    Returns:
        Tuple of (line_trace, cone_trace)
    """
    end = start + direction

    # Line trace
    line_trace = go.Scatter3d(
        x=[start[0], end[0]],
        y=[start[1], end[1]],
        z=[start[2], end[2]],
        mode='lines',
        line=dict(color=color, width=4),
        showlegend=showlegend,
        name=name,
        hoverinfo='skip'
    )

    # Cone for arrow head
    cone_trace = go.Cone(
        x=[end[0]],
        y=[end[1]],
        z=[end[2]],
        u=[direction[0] * 0.3],
        v=[direction[1] * 0.3],
        w=[direction[2] * 0.3],
        colorscale=[[0, color], [1, color]],
        showscale=False,
        showlegend=False,
        hoverinfo='skip',
        sizemode='absolute',
        sizeref=2
    )

    return line_trace, cone_trace


def plot_trajectory_3d(data: Dict[str, Any], arrow_interval: int = 1,
                       arrow_length: float = 10.0, output_html: str = None) -> None:
    """
    Plot trajectory in 3D space with orientation arrows using Plotly

    Args:
        data: Trajectory data dictionary
        arrow_interval: Show arrow every N points (1 = every point)
        arrow_length: Length of orientation arrows in mm
        output_html: Optional path to save HTML file
    """
    trajectory = data['trajectory']

    if len(trajectory) == 0:
        print("エラー: 軌跡データが空です")
        return

    # Extract positions and metadata
    positions = np.array([
        [p['translation']['x'], p['translation']['y'], p['translation']['z']]
        for p in trajectory
    ])

    timestamps = np.array([p['timestamp'] for p in trajectory])

    # Create hover text for trajectory points
    hover_texts = []
    for i, pose in enumerate(trajectory):
        text = (
            f"<b>Point {i}</b><br>"
            f"Time: {pose['timestamp']:.3f}s<br>"
            f"X: {pose['translation']['x']:.2f}mm<br>"
            f"Y: {pose['translation']['y']:.2f}mm<br>"
            f"Z: {pose['translation']['z']:.2f}mm<br>"
            f"Roll: {pose['rotation']['roll']:.2f}°<br>"
            f"Pitch: {pose['rotation']['pitch']:.2f}°<br>"
            f"Yaw: {pose['rotation']['yaw']:.2f}°<br>"
            f"Quality: {pose.get('quality', 0):.3f}"
        )
        hover_texts.append(text)

    # Create figure
    fig = go.Figure()

    # Add trajectory line with color gradient based on time
    fig.add_trace(go.Scatter3d(
        x=positions[:, 0],
        y=positions[:, 1],
        z=positions[:, 2],
        mode='lines+markers',
        line=dict(
            color=timestamps,
            colorscale='Viridis',
            width=4,
            colorbar=dict(
                title="Time (s)",
                thickness=20,
                len=0.7
            )
        ),
        marker=dict(
            size=2,
            color=timestamps,
            colorscale='Viridis',
            showscale=False
        ),
        text=hover_texts,
        hoverinfo='text',
        name='Trajectory',
        showlegend=True
    ))

    # Add start and end markers
    fig.add_trace(go.Scatter3d(
        x=[positions[0, 0]],
        y=[positions[0, 1]],
        z=[positions[0, 2]],
        mode='markers',
        marker=dict(size=6, color='green', symbol='diamond', line=dict(color='darkgreen', width=1)),
        name='🟢 Start (開始点)',
        hovertext=f"<b>START</b><br>{hover_texts[0]}",
        hoverinfo='text',
        showlegend=True
    ))

    fig.add_trace(go.Scatter3d(
        x=[positions[-1, 0]],
        y=[positions[-1, 1]],
        z=[positions[-1, 2]],
        mode='markers',
        marker=dict(size=6, color='red', symbol='diamond', line=dict(color='darkred', width=1)),
        name='🔴 End (終了点)',
        hovertext=f"<b>END</b><br>{hover_texts[-1]}",
        hoverinfo='text',
        showlegend=True
    ))

    # Add orientation arrows at selected points
    for i in range(0, len(trajectory), arrow_interval):
        pose = trajectory[i]
        pos = positions[i]

        # Get rotation matrix from Euler angles
        R = rotation_matrix_from_euler(
            pose['rotation']['roll'],
            pose['rotation']['pitch'],
            pose['rotation']['yaw']
        )

        # Direction vectors (in camera frame)
        directions = np.eye(3) * arrow_length

        # Transform to world frame
        world_dirs = R @ directions

        # Color based on time (normalized)
        time_norm = timestamps[i] / timestamps[-1] if timestamps[-1] > 0 else 0
        # Viridis colormap approximation
        z_color = f'rgb({int(68 + time_norm * (253-68))}, {int(1 + time_norm * (231-1))}, {int(84 + time_norm * (37-84))})'

        # Add arrows (only show legend for first set)
        show_legend = (i == 0)

        # X-axis (red)
        line, cone = create_arrow_trace(pos, world_dirs[:, 0], 'red', 'X-axis', show_legend)
        fig.add_trace(line)
        fig.add_trace(cone)

        # Y-axis (green)
        line, cone = create_arrow_trace(pos, world_dirs[:, 1], 'green', 'Y-axis', show_legend)
        fig.add_trace(line)
        fig.add_trace(cone)

        # Z-axis (time-colored)
        line, cone = create_arrow_trace(pos, world_dirs[:, 2], z_color, 'Z-axis', show_legend)
        fig.add_trace(line)
        fig.add_trace(cone)

    # Build title with metadata
    metadata = data.get('metadata', {})
    num_poses = metadata.get('num_poses', len(trajectory))
    duration = metadata.get('duration_sec', 0)

    title = f'<b>Camera Trajectory 3D View</b><br>'
    title += f'Poses: {num_poses} | Duration: {duration:.2f}s'

    if 'total_displacement' in data and data['total_displacement']:
        disp = data['total_displacement']
        displacement_vals = disp.get('displacement', {})

        dx = displacement_vals.get('x_mm', 0)
        dy = displacement_vals.get('y_mm', 0)
        dz = displacement_vals.get('z_mm', 0)
        dyaw = displacement_vals.get('yaw_deg', 0)

        dist_2d = disp.get('distance_2d_mm', 0)
        dist_3d = disp.get('distance_3d_mm', 0)

        title += f'<br>Displacement: ΔX={dx:+.2f}mm, ΔY={dy:+.2f}mm, ΔZ={dz:+.2f}mm'
        title += f'<br>Rotation: ΔYaw={dyaw:+.2f}° | Distance: 2D={dist_2d:.2f}mm, 3D={dist_3d:.2f}mm'

    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=14)
        ),
        scene=dict(
            xaxis=dict(title='X (mm)', backgroundcolor="rgb(230, 230,230)", gridcolor="white"),
            yaxis=dict(title='Y (mm)', backgroundcolor="rgb(230, 230,230)", gridcolor="white"),
            zaxis=dict(title='Z (mm)', backgroundcolor="rgb(230, 230,230)", gridcolor="white"),
            aspectmode='data'
        ),
        width=1200,
        height=900,
        showlegend=True,
        legend=dict(
            x=1.0,
            y=1.0,
            xanchor='right',
            yanchor='top'
        ),
        hovermode='closest'
    )

    # Print info
    print(f"軌跡を表示しています...")
    print(f"  ポーズ数: {num_poses}")
    print(f"  期間: {duration:.2f}秒")
    if 'total_displacement' in data and data['total_displacement']:
        disp = data['total_displacement']
        displacement_vals = disp.get('displacement', {})
        print(f"\n  移動量:")
        print(f"    ΔX: {displacement_vals.get('x_mm', 0):+.2f}mm")
        print(f"    ΔY: {displacement_vals.get('y_mm', 0):+.2f}mm")
        print(f"    ΔZ: {displacement_vals.get('z_mm', 0):+.2f}mm")
        print(f"    ΔYaw: {displacement_vals.get('yaw_deg', 0):+.2f}°")
        print(f"\n  総移動距離:")
        print(f"    2D: {disp.get('distance_2d_mm', 0):.2f}mm")
        print(f"    3D: {disp.get('distance_3d_mm', 0):.2f}mm")
    print(f"\n矢印の意味:")
    print(f"  赤: X軸 (右)")
    print(f"  緑: Y軸 (下)")
    print(f"  青→紫: Z軸 (前) - 時間経過を色で表示")
    print(f"\nインタラクティブ操作:")
    print(f"  - マウスドラッグ: 回転")
    print(f"  - スクロール: ズーム")
    print(f"  - ポイントにホバー: 詳細情報表示")

    # Save to HTML if specified
    if output_html:
        fig.write_html(output_html)
        print(f"\nHTMLファイルを保存しました: {output_html}")
        print(f"ブラウザで開いてインタラクティブに操作できます")

    # Show interactive plot
    fig.show()


def main():
    parser = argparse.ArgumentParser(
        description='3D trajectory visualization tool for ChArUco camera tracking (Plotly version)'
    )
    parser.add_argument('trajectory_file', type=str,
                       help='Path to trajectory YAML file')
    parser.add_argument('--interval', type=int, default=10,
                       help='Show orientation arrow every N points (default: 10)')
    parser.add_argument('--arrow-length', type=float, default=10.0,
                       help='Length of orientation arrows in mm (default: 10.0)')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Save interactive plot as HTML file')

    args = parser.parse_args()

    # Load trajectory data
    print(f"軌跡データを読み込んでいます: {args.trajectory_file}")
    data = load_trajectory(args.trajectory_file)

    # Plot trajectory
    plot_trajectory_3d(data, arrow_interval=args.interval,
                      arrow_length=args.arrow_length,
                      output_html=args.output)


if __name__ == '__main__':
    main()
