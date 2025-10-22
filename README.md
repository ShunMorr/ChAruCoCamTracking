# ChArUco Camera Tracking System

## 概要

ChArUcoボード上をカメラで移動した際の軌跡を高精度（目標誤差0.1mm以下）でトラッキングするシステムです。カメラの移動量・回転量の精密な計測に使用します。

![gif](./doc/test.gif)
- [グラフ](https://htmlpreview.github.io/?https://github.com/ShunMorr/ChAruCoCamTracking/blob/main/doc/track_test.html)

## 特徴

- **高精度位置測定**: ChArUcoボードとOpenCVを使用した高精度ポーズ推定
- **連続トラッキング**: リアルタイムでカメラ位置(x, y, yaw)の軌跡を記録
- **スポット測定**: 特定地点での高精度位置測定（複数サンプル平均化）
- **位置比較**: 測定結果の比較による移動量計算
- **YAML出力**: 測定結果をYAML形式で保存
- **スレッド化カメラ**: 別スレッドでの画像取得により常に最新フレームを処理
- **リアルタイムFPS表示**: キャプチャFPSとトラッキングFPSを表示
- **可変トラッキング周波数**: データ記録頻度を設定可能（CPU負荷削減）

## システム要件

- Python 3.8以上
- Webカメラまたはカメラデバイス
- ChArUcoボード（印刷物または表示デバイス）

## インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd ChAruCoCamTracking

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使用方法

### 1. ChArUcoボードの準備

まず、使用するChArUcoボード画像を生成します：

```bash
python cli.py generate-board -o board.png --size 3000
```

生成された画像を印刷するか、ディスプレイに表示します。

**印刷時の注意点:**
- 実際のマスサイズが設定値（デフォルト40mm）と一致するように印刷してください
- 高品質な印刷を使用してください（レーザープリンター推奨）
- 平坦な面に貼り付けてください

### 2. カメラキャリブレーション

カメラの内部パラメータと歪み係数を取得します：

```bash
python cli.py calibrate
```

**操作方法:**
- ChArUcoボードを様々な角度・位置でカメラに映します
- `SPACE`: フレーム取得（最低30フレーム必要）
- `C`: キャリブレーション実行
- `Q`: 終了

キャリブレーション結果は `calibration_params.yaml` に保存されます。

### 3. 連続軌跡トラッキング

カメラを連続的に移動させながら、カメラ位置の軌跡を記録します：

```bash
python cli.py track -o trajectory_test1.yaml
```

**操作方法:**
- `S`: トラッキング開始
- `E`: トラッキング終了・保存
- `Q`: 中止

**リアルタイムCLI出力:**
トラッキング中、ターミナルに以下の情報が同じ行に更新表示されます：
```
Poses:  123 | X:  234.567mm | Y:  123.456mm | Z:  450.123mm | Yaw:   45.67° | Quality: 0.95 | FPS: 23.5
```

出力ファイルには以下が含まれます：
- 各時刻でのカメラ位置(x, y, z, roll, pitch, yaw)
- 総移動距離・移動量
- トラッキング品質情報

### 4. スポット測定

特定地点での高精度位置測定を行います：

```bash
# 移動前の位置測定
python cli.py spot -o spot_before.yaml -s 50

# カメラを移動...

# 移動後の位置測定
python cli.py spot -o spot_after.yaml -s 50
```

**操作方法:**
- カメラをChArUcoボード上に配置
- `SPACE`: 測定実行（指定サンプル数を自動収集・平均化）
- `Q`: 終了

**リアルタイムCLI出力:**
サンプル収集中、進捗がターミナルに表示されます：
```
サンプル収集中:  35/50 ( 70.0%) | Quality: 0.95
```

測定完了後、詳細な結果が表示されます：
```
測定完了: 50/50 サンプル使用
位置: X=234.567mm, Y=123.456mm, Z=450.123mm
回転: Yaw=45.678°
標準偏差: X=0.0123mm, Y=0.0156mm, Z=0.0234mm
```

オプション:
- `-s, --samples N`: 平均化サンプル数（デフォルト: 30）

### 5. 測定結果の比較

#### スポット測定の比較

2つのスポット測定を比較して移動量を計算します：

```bash
python cli.py compare spot \
  --file1 spot_before.yaml \
  --file2 spot_after.yaml \
  -o displacement.yaml
```

#### 軌跡の開始・終了比較

軌跡データの開始位置と終了位置を比較します：

```bash
python cli.py compare trajectory \
  --file1 trajectory_test1.yaml \
  -o trajectory_displacement.yaml
```

出力には以下が含まれます：
- X, Y, Z方向の移動量（mm単位）
- Yaw回転角度（度単位）
- 2D/3D移動距離
- 測定不確かさ（スポット測定の場合）

### 6. 軌跡データの可視化

yamlファイルを読み込んで軌跡データをプロットします

```bash
python view.py file1_trajectory_test1.yaml --interval 5 --arrow_length 20 -o file1_trajectory_test1.html
``` 

オプション
- `-o, --output`: 出力ファイル
- `--interval N`: N点ごとに姿勢の矢印を表示(Default=10)
- `--arrow-length L`: 矢印の長さ

## 設定ファイル

`config.yaml` でシステムパラメータを設定できます：

```yaml
charuco:
  dictionary: "DICT_5X5_100"  # ArUco辞書タイプ
  squares_x: 7                # チェスボード幅（マス数）
  squares_y: 7                # チェスボード高さ（マス数）
  square_length: 0.03         # 1マスのサイズ (m)
  marker_length: 0.022        # マーカーサイズ (m)

camera:
  device_id: 0                # カメラデバイスID
  width: 1280                 # 解像度（幅）
  height: 720                 # 解像度（高さ）
  fps: 30                     # フレームレート

calibration:
  save_path: "calibration_params.yaml"
  min_frames: 30              # 最小キャリブレーションフレーム数

tracking:
  tracking_fps: 10            # トラッキング処理のFPS（データ記録頻度）
  default_save_path: "trajectory.yaml"
  spot_save_path: "spot_measurement.yaml"

display:
  enabled: true               # GUI表示の有効/無効
```

## 出力データ形式

### スポット測定 (spot_measurement.yaml)

```yaml
metadata:
  timestamp: "2025-01-15T10:30:00"
  measurement_type: "spot"

pose:
  translation:
    x: 123.456  # mm
    y: 234.567  # mm
    z: 450.123  # mm
  rotation:
    roll: 0.123   # degrees
    pitch: -0.234 # degrees
    yaw: 45.678   # degrees
  quality: 0.95
  num_samples: 50
  std_dev:
    x_mm: 0.012
    y_mm: 0.015
    z_mm: 0.020
```

### 軌跡データ (trajectory.yaml)

```yaml
metadata:
  num_poses: 150
  duration_sec: 5.2
  timestamp: "2025-01-15T10:35:00"

trajectory:
  - timestamp: 0.0
    translation: {x: 0.0, y: 0.0, z: 450.0}
    rotation: {roll: 0.0, pitch: 0.0, yaw: 0.0}
    quality: 0.95
    num_corners: 35
  # ... 以降の各時刻のポーズ

total_displacement:
  displacement:
    x_mm: 100.5
    y_mm: 50.3
    z_mm: 0.2
    yaw_deg: 15.8
  distance_2d_mm: 112.3
  distance_3d_mm: 112.3
```

### 比較結果 (comparison.yaml)

```yaml
metadata:
  comparison_type: "spot_to_spot"
  file1: "spot_before.yaml"
  file2: "spot_after.yaml"

displacement:
  displacement:
    x_mm: 100.234
    y_mm: -50.123
    z_mm: 0.456
    yaw_deg: 15.678
  distance_2d_mm: 112.067
  distance_3d_mm: 112.068
```

## パフォーマンスと更新周波数

### スレッド化カメラキャプチャ

本システムは**スレッド化カメラキャプチャ**を採用しており、以下の利点があります：

- **低レイテンシー**: 画像取得を別スレッドで実行し、常に最新フレームを処理
- **フレームバッファ問題の解消**: 処理が遅くても古いフレームが溜まらない
- **正確なタイムスタンプ**: 実際のカメラ位置と処理フレームの時間差を最小化

### 期待される更新周波数

実際の更新周波数は以下の要因に依存します：

1. **カメラFPS**: config.yamlで設定（デフォルト30fps）
2. **トラッキングFPS**: config.yamlで設定（デフォルト10fps）
   - データ記録とポーズ推定の実行頻度
   - 1, 5, 10, 30など、用途に応じて調整可能
3. **処理性能**:
   - ChArUco検出: 約10-30ms（解像度とコーナー数に依存）
   - ポーズ推定: 約1-5ms
   - tracking_fps=10の場合、CPU負荷は大幅に削減

4. **実測値の例**:
   - 1280x720解像度、Intel i7プロセッサ
   - キャプチャFPS: 30fps
   - トラッキングFPS: 9.8/10fps（ボード検出成功時）

### FPS表示

トラッキング時に画面下部に2つのFPS値が表示されます：

- **Capture FPS**: カメラからのフレーム取得速度
- **Tracking FPS**: 実際のデータ記録速度/目標速度（例: 9.8/10 fps）

**tracking_fpsの設定:**
- `config.yaml`の`tracking.tracking_fps`でデータ記録頻度を設定可能
- tracking_fps=10の場合、0.1秒ごとにポーズ推定とデータ記録を実行
- スキップされたフレームでは計算を行わないため、CPU負荷を削減
- GUIには最後に計算した座標が継続表示されます（点滅なし）

## 高精度化のためのヒント

### 1. ハードウェアセットアップ
- 高解像度カメラを使用（1920x1080以上推奨）
- カメラをしっかりと固定
- 均一な照明を確保
- 高品質なChArUcoボード（平坦で歪みのない）

### 2. キャリブレーション
- 多数のフレームを収集（50フレーム以上推奨）
- ボードを様々な角度・距離で撮影
- 再投影誤差が0.5ピクセル以下を目標

### 3. 測定時
- スポット測定では多数のサンプルを平均化（50-100サンプル）
- カメラとボードが相対的に静止している状態で測定
- 十分な数のコーナーが検出されていることを確認（quality > 0.8）
- 測定不確かさ（標準偏差）を確認

### 4. 環境
- 振動の少ない環境
- 安定した照明
- ChArUcoボードの反射を避ける

## トラブルシューティング

### ボードが検出されない
- 照明を改善
- カメラのフォーカスを調整
- ボードとカメラの距離を調整
- config.yamlのマーカーサイズ設定を確認

### 精度が低い
- キャリブレーションをやり直す
- より多くのサンプルを収集
- カメラの固定を確認
- ボードの平坦性を確認

### カメラが開けない
- デバイスIDを確認（config.yamlのdevice_id）
- 他のアプリケーションがカメラを使用していないか確認

## ライセンス

MIT License

## 参考文献

- OpenCV ArUco module documentation
- "Automatic generation and detection of highly reliable fiducial markers under occlusion" (Garrido-Jurado et al., 2014)
