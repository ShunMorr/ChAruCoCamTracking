#!/usr/bin/env python3
"""
Simple viewer for trajectory test results.
Creates time-series plots for x, y, and yaw from trajectory YAML files.
"""

import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import argparse
from pathlib import Path


def load_trajectory_data(yaml_file):
    """Load trajectory data from YAML file."""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data


def extract_time_series(trajectory_data, min_quality=None, min_corners=None):
    """Extract time series data for x, y, yaw with optional filtering."""
    timestamps = []
    x_values = []
    y_values = []
    yaw_values = []
    filtered_count = 0

    for pose in trajectory_data['trajectory']:
        # Apply filters
        if min_quality is not None and pose.get('quality', 0) < min_quality:
            filtered_count += 1
            continue
        if min_corners is not None and pose.get('num_corners', 0) < min_corners:
            filtered_count += 1
            continue

        timestamps.append(float(pose['timestamp']))
        x_values.append(pose['translation']['x'])
        y_values.append(pose['translation']['y'])
        yaw_values.append(pose['rotation']['yaw'])

    # Convert to relative time (start from 0)
    if timestamps:
        base_time = timestamps[0]
        timestamps = [t - base_time for t in timestamps]

    return timestamps, x_values, y_values, yaw_values, filtered_count


def plot_trajectory(yaml_file, output_file=None, min_quality=None, min_corners=None):
    """Create time-series plots for x, y, and yaw."""
    # Load data
    data = load_trajectory_data(yaml_file)
    timestamps, x_values, y_values, yaw_values, filtered_count = extract_time_series(
        data, min_quality, min_corners
    )

    # Create figure with 3 subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('X Position over Time', 'Y Position over Time', 'Yaw Angle over Time'),
        vertical_spacing=0.1
    )

    # Plot X
    fig.add_trace(
        go.Scatter(x=timestamps, y=x_values, mode='lines', name='X', line=dict(color='blue', width=2)),
        row=1, col=1
    )
    fig.update_yaxes(title_text="X (mm)", row=1, col=1)

    # Plot Y
    fig.add_trace(
        go.Scatter(x=timestamps, y=y_values, mode='lines', name='Y', line=dict(color='green', width=2)),
        row=2, col=1
    )
    fig.update_yaxes(title_text="Y (mm)", row=2, col=1)

    # Plot Yaw
    fig.add_trace(
        go.Scatter(x=timestamps, y=yaw_values, mode='lines', name='Yaw', line=dict(color='red', width=2)),
        row=3, col=1
    )
    fig.update_yaxes(title_text="Yaw (degrees)", row=3, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=3, col=1)

    # Update layout with filter info
    title_parts = [f'Trajectory Time Series: {Path(yaml_file).name}']
    if min_quality is not None or min_corners is not None:
        filter_info = []
        if min_quality is not None:
            filter_info.append(f'quality≥{min_quality}')
        if min_corners is not None:
            filter_info.append(f'corners≥{min_corners}')
        title_parts.append(f' (Filtered: {", ".join(filter_info)})')

    fig.update_layout(
        title_text=''.join(title_parts),
        height=900,
        showlegend=True,
        hovermode='x unified'
    )

    # Save or show
    if output_file:
        fig.write_html(output_file)
        print(f"Plot saved to: {output_file}")
    else:
        fig.show()

    # Print summary statistics
    print("\n=== Summary Statistics ===")
    total_poses = len(data['trajectory'])
    print(f"Total poses in file: {total_poses}")
    if filtered_count > 0:
        print(f"Filtered out: {filtered_count} poses")
        print(f"Displayed poses: {len(timestamps)} ({len(timestamps)/total_poses*100:.1f}%)")
    else:
        print(f"Displayed poses: {len(timestamps)}")

    if len(timestamps) > 0:
        print(f"Duration: {timestamps[-1]:.2f} seconds")
        print(f"\nX: min={min(x_values):.2f}, max={max(x_values):.2f}, range={max(x_values)-min(x_values):.2f} mm")
        print(f"Y: min={min(y_values):.2f}, max={max(y_values):.2f}, range={max(y_values)-min(y_values):.2f} mm")
        print(f"Yaw: min={min(yaw_values):.2f}, max={max(yaw_values):.2f}, range={max(yaw_values)-min(yaw_values):.2f} deg")
    else:
        print("\nWarning: No data points match the filter criteria!")


def main():
    parser = argparse.ArgumentParser(
        description='Visualize trajectory test results as time-series plots for x, y, and yaw.'
    )
    parser.add_argument(
        'yaml_file',
        type=str,
        help='Path to trajectory YAML file'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file path for the plot (e.g., output.html). If not specified, plot will be displayed in browser.'
    )
    parser.add_argument(
        '--min-quality',
        type=float,
        default=None,
        help='Minimum quality threshold for filtering poses (e.g., 0.5)'
    )
    parser.add_argument(
        '--min-corners',
        type=int,
        default=None,
        help='Minimum number of corners for filtering poses (e.g., 4)'
    )

    args = parser.parse_args()

    # Check if file exists
    if not Path(args.yaml_file).exists():
        print(f"Error: File not found: {args.yaml_file}")
        return

    # Create plots
    plot_trajectory(args.yaml_file, args.output, args.min_quality, args.min_corners)


if __name__ == '__main__':
    main()
