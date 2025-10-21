#!/usr/bin/env python3
"""
ChArUco Camera Tracking System - CLI Interface
AMR高精度位置トラッキングシステム
"""
import argparse
import sys
from pathlib import Path

from src.utils import load_yaml
from src.calibration import run_calibration_interactive, CameraCalibrator
from src.trajectory_tracker import run_trajectory_tracking
from src.spot_measurement import run_spot_measurement
from src.position_compare import compare_spot_measurements, compare_trajectory_endpoints


def load_config(config_file: str = 'config.yaml'):
    """Load configuration file"""
    try:
        return load_yaml(config_file)
    except Exception as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)


def cmd_calibrate(args):
    """Run camera calibration"""
    config = load_config(args.config)

    print("=== カメラキャリブレーション ===")
    result_file = run_calibration_interactive(config)

    if result_file:
        print(f"\nキャリブレーション完了!")
        print(f"パラメータ保存先: {result_file}")
    else:
        print("\nキャリブレーションが中断されました")
        sys.exit(1)


def cmd_track(args):
    """Run continuous trajectory tracking"""
    config = load_config(args.config)

    # Load calibration parameters
    calib_file = args.calibration or config['calibration']['save_path']
    if not Path(calib_file).exists():
        print(f"キャリブレーションファイルが見つかりません: {calib_file}")
        print("先に 'calibrate' コマンドでキャリブレーションを実行してください")
        sys.exit(1)

    try:
        calibration_params = CameraCalibrator.load_calibration(calib_file)
    except Exception as e:
        print(f"キャリブレーションパラメータの読み込みに失敗しました: {e}")
        sys.exit(1)

    # Set output file
    output_file = args.output or config['tracking']['default_save_path']

    print("=== 連続軌跡トラッキング ===")
    result_file = run_trajectory_tracking(config, calibration_params, output_file)

    if result_file:
        print(f"\n軌跡データ保存完了: {result_file}")
    else:
        print("\nトラッキングが中断されました")
        sys.exit(1)


def cmd_spot(args):
    """Run spot measurement"""
    config = load_config(args.config)

    # Load calibration parameters
    calib_file = args.calibration or config['calibration']['save_path']
    if not Path(calib_file).exists():
        print(f"キャリブレーションファイルが見つかりません: {calib_file}")
        print("先に 'calibrate' コマンドでキャリブレーションを実行してください")
        sys.exit(1)

    try:
        calibration_params = CameraCalibrator.load_calibration(calib_file)
    except Exception as e:
        print(f"キャリブレーションパラメータの読み込みに失敗しました: {e}")
        sys.exit(1)

    # Set output file
    output_file = args.output or config['tracking']['spot_save_path']

    # Set number of samples
    num_samples = args.samples or 30

    print("=== スポット測定 ===")
    result_file = run_spot_measurement(config, calibration_params, output_file, num_samples)

    if result_file:
        print(f"\n測定データ保存完了: {result_file}")
    else:
        print("\n測定が中断されました")
        sys.exit(1)


def cmd_compare(args):
    """Compare two measurements"""
    if args.mode == 'spot':
        # Compare two spot measurements
        if not args.file1 or not args.file2:
            print("エラー: spot モードでは --file1 と --file2 が必要です")
            sys.exit(1)

        output_file = args.output or 'spot_comparison.yaml'

        print("=== スポット測定比較 ===")
        success = compare_spot_measurements(args.file1, args.file2, output_file)

        if not success:
            sys.exit(1)

    elif args.mode == 'trajectory':
        # Compare trajectory endpoints
        if not args.file1:
            print("エラー: trajectory モードでは --file1（軌跡ファイル）が必要です")
            sys.exit(1)

        output_file = args.output or 'trajectory_comparison.yaml'

        print("=== 軌跡端点比較 ===")
        success = compare_trajectory_endpoints(args.file1, output_file)

        if not success:
            sys.exit(1)

    else:
        print(f"エラー: 不明な比較モード: {args.mode}")
        sys.exit(1)


def cmd_generate_board(args):
    """Generate ChArUco board image"""
    config = load_config(args.config)
    charuco_config = config['charuco']

    import cv2
    import numpy as np

    # Setup ArUco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(
        getattr(cv2.aruco, charuco_config['dictionary'])
    )

    # Create ChArUco board
    board = cv2.aruco.CharucoBoard(
        (charuco_config['squares_x'], charuco_config['squares_y']),
        charuco_config['square_length'],
        charuco_config['marker_length'],
        aruco_dict
    )

    # Generate board image
    img_size = args.size or 2000
    board_img = board.generateImage((img_size, img_size), marginSize=int(img_size * 0.05))

    # Save image
    output_file = args.output or 'charuco_board.png'
    cv2.imwrite(output_file, board_img)

    print(f"ChArUcoボード画像を生成しました: {output_file}")
    print(f"画像サイズ: {img_size}x{img_size} pixels")
    print(f"マス数: {charuco_config['squares_x']}x{charuco_config['squares_y']}")
    print(f"マスサイズ: {charuco_config['square_length']*1000}mm")
    print(f"マーカーサイズ: {charuco_config['marker_length']*1000}mm")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ChArUco Camera Tracking System - AMR高精度位置トラッキング',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # キャリブレーション
  python cli.py calibrate

  # 連続トラッキング
  python cli.py track -o trajectory_1.yaml

  # スポット測定
  python cli.py spot -o spot_before.yaml
  python cli.py spot -o spot_after.yaml

  # 測定比較
  python cli.py compare spot --file1 spot_before.yaml --file2 spot_after.yaml -o comparison.yaml

  # ChArUcoボード生成
  python cli.py generate-board -o board.png --size 3000
        """
    )

    parser.add_argument('-c', '--config', default='config.yaml',
                        help='設定ファイルのパス (default: config.yaml)')

    subparsers = parser.add_subparsers(dest='command', help='コマンド')

    # Calibrate command
    parser_calib = subparsers.add_parser('calibrate', help='カメラキャリブレーション')

    # Track command
    parser_track = subparsers.add_parser('track', help='連続軌跡トラッキング')
    parser_track.add_argument('-o', '--output', help='出力ファイル名')
    parser_track.add_argument('--calibration', help='キャリブレーションファイルのパス')

    # Spot command
    parser_spot = subparsers.add_parser('spot', help='スポット測定')
    parser_spot.add_argument('-o', '--output', help='出力ファイル名')
    parser_spot.add_argument('--calibration', help='キャリブレーションファイルのパス')
    parser_spot.add_argument('-s', '--samples', type=int, help='平均化サンプル数 (default: 30)')

    # Compare command
    parser_compare = subparsers.add_parser('compare', help='測定比較')
    parser_compare.add_argument('mode', choices=['spot', 'trajectory'],
                                help='比較モード (spot: 2つのスポット測定比較, trajectory: 軌跡の開始・終了比較)')
    parser_compare.add_argument('--file1', help='1つ目の測定ファイル（またはtrajectoryモードでは軌跡ファイル）')
    parser_compare.add_argument('--file2', help='2つ目の測定ファイル（spotモードのみ）')
    parser_compare.add_argument('-o', '--output', help='出力ファイル名')

    # Generate board command
    parser_gen = subparsers.add_parser('generate-board', help='ChArUcoボード画像生成')
    parser_gen.add_argument('-o', '--output', help='出力ファイル名 (default: charuco_board.png)')
    parser_gen.add_argument('--size', type=int, help='画像サイズ（ピクセル）(default: 2000)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'calibrate':
        cmd_calibrate(args)
    elif args.command == 'track':
        cmd_track(args)
    elif args.command == 'spot':
        cmd_spot(args)
    elif args.command == 'compare':
        cmd_compare(args)
    elif args.command == 'generate-board':
        cmd_generate_board(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
