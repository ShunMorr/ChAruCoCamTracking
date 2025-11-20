# ChArUco Camera Tracking - Android版

Android端末でChArUcoボードを使った高精度カメラトラッキングを実現するアプリケーションです。

## 概要

このAndroidアプリは、ChArUcoボード（チェスボードとArUcoマーカーを組み合わせたもの）を使用して、カメラの位置と姿勢を高精度でトラッキングします。Python版の主要機能をAndroidに移植しています。

## 主な機能

- **カメラキャリブレーション**: カメラの内部パラメータと歪み係数を取得
- **連続軌跡トラッキング**: リアルタイムでカメラ位置(x, y, yaw)の軌跡を記録
- **スポット測定**: 特定地点での高精度位置測定（複数サンプル平均化）
- **YAML出力**: 測定結果をYAML形式で保存

## システム要件

- Android 7.0 (API level 24) 以上
- カメラ搭載のAndroid端末
- ChArUcoボード（印刷物または表示デバイス）

## セットアップ手順

### クイックスタート（推奨）

OpenCVは自動的にMaven経由でダウンロードされるため、追加のセットアップは不要です：

```bash
cd android
./build-release.sh
```

これにより、ビルド済みAPKが生成されます。

### 詳細なセットアップ

#### 1. OpenCVについて

**自動セットアップ（推奨）**: OpenCVはMaven経由で自動的に取得されます（`build.gradle.kts`で設定済み）

**手動セットアップ（オプション）**: 公式SDKを使用したい場合：
1. [OpenCV公式サイト](https://opencv.org/releases/)からAndroid SDKをダウンロード
2. `opencv-4.x.x.aar` を `android/app/libs/` にコピー
3. `build.gradle.kts`のOpenCV依存関係をコメントアウトして手動の設定に切り替え

#### 2. デバッグAPKのビルド（開発・テスト用）

```bash
cd android
./gradlew assembleDebug
```

生成されるAPK: `app/build/outputs/apk/debug/app-debug.apk`

#### 3. リリースAPKのビルド（配布用）

詳細な手順は [BUILD_RELEASE.md](BUILD_RELEASE.md) を参照してください。

**クイックガイド**:

```bash
# 1. 署名鍵を作成（初回のみ）
keytool -genkey -v -keystore app/charuco-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias charuco-key

# 2. keystore.propertiesを作成
cat > keystore.properties << 'EOF'
storePassword=YOUR_PASSWORD
keyPassword=YOUR_PASSWORD
keyAlias=charuco-key
storeFile=app/charuco-release-key.jks
EOF

# 3. ビルド
./build-release.sh
```

生成されるAPK: `app/build/outputs/apk/release/app-release.apk`

### 4. アプリのインストール

```bash
./gradlew installDebug
```

または、Android Studioで実行ボタンをクリック

## 使用方法

### 1. ChArUcoボードの準備

Python版のCLIツールを使用してChArUcoボード画像を生成します：

```bash
cd ..  # プロジェクトルートに移動
python cli.py generate-board -o board.png --size 3000
```

生成された画像を印刷するか、タブレットなどに表示します。

**印刷時の注意点:**
- 実際のマスサイズが設定値（デフォルト40mm）と一致するように印刷してください
- 高品質な印刷を使用してください（レーザープリンター推奨）
- 平坦な面に貼り付けてください

### 2. カメラキャリブレーション

アプリを起動し、「カメラキャリブレーション」ボタンをタップします。

**操作方法:**
1. ChArUcoボードを様々な角度・位置でカメラに映します
2. 「フレーム取得」ボタンを長押ししてフレームを取得（最低30フレーム必要）
3. 十分なフレームを取得したら「キャリブレーション実行」ボタンをタップ
4. キャリブレーション完了後、自動的にメイン画面に戻ります

### 3. 連続軌跡トラッキング

「連続トラッキング」ボタンをタップします。

**操作方法:**
1. 「トラッキング開始」ボタンをタップ
2. カメラを移動させながら軌跡を記録
3. 「トラッキング終了」ボタンをタップ
4. ファイル名を入力して保存

**リアルタイム表示:**
- 記録ポーズ数
- X, Y, Z座標（mm単位）
- Yaw回転角度（度単位）
- 検出品質スコア
- FPS

### 4. スポット測定

「スポット測定」ボタンをタップします。

**操作方法:**
1. カメラをChArUcoボード上の測定位置に配置
2. 「測定開始」ボタンをタップ
3. 自動的に30サンプルを収集・平均化
4. 測定完了後、結果が表示されます
5. ファイル名を入力して保存

**測定結果:**
- 平均位置（X, Y, Z）
- 平均回転角度（Yaw）
- 標準偏差（精度の指標）

### 5. データの取り出し

測定データは端末の `Documents` フォルダに保存されます：
- パス: `/Android/data/com.charuco.tracking/files/Documents/`

ファイルエクスプローラーアプリでアクセスするか、USBでPCに接続して取り出せます。

## 設定のカスタマイズ

アプリの設定は `ConfigManager.kt` で定義されています。デフォルト値を変更する場合は、以下の定数を編集してください：

```kotlin
// ChArUco Board Configuration
const val DEFAULT_DICTIONARY = "DICT_5X5_100"
const val DEFAULT_SQUARES_X = 7
const val DEFAULT_SQUARES_Y = 7
const val DEFAULT_SQUARE_LENGTH = 0.04  // meters
const val DEFAULT_MARKER_LENGTH = 0.03  // meters

// Tracking Configuration
const val DEFAULT_TRACKING_FPS = 10
const val DEFAULT_MIN_CALIBRATION_FRAMES = 30
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
  num_samples: 30
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

total_displacement:
  displacement:
    x_mm: 100.5
    y_mm: 50.3
    z_mm: 0.2
    yaw_deg: 15.8
  distance_2d_mm: 112.3
  distance_3d_mm: 112.3
```

## アーキテクチャ

### パッケージ構成

```
com.charuco.tracking
├── calibration/          # キャリブレーション関連
│   └── CameraCalibrator.kt
├── detector/             # ChArUco検出
│   └── CharucoDetector.kt
├── tracking/             # トラッキング機能
│   ├── TrajectoryTracker.kt
│   └── SpotMeasurer.kt
├── ui/                   # UIコンポーネント
│   ├── MainActivity.kt
│   ├── CalibrationActivity.kt
│   ├── TrackingActivity.kt
│   └── SpotMeasurementActivity.kt
└── utils/                # ユーティリティ
    ├── CalibrationManager.kt
    ├── ConfigManager.kt
    ├── DataExporter.kt
    └── PoseData.kt
```

### 使用ライブラリ

- **OpenCV for Android**: 画像処理とChArUco検出
- **CameraX**: カメラアクセスとプレビュー
- **SnakeYAML**: YAML形式でのデータ保存
- **Material Components**: UI要素
- **Kotlin Coroutines**: 非同期処理

## トラブルシューティング

### ビルドエラー

**OpenCVが見つからない:**
- `android/app/libs/` ディレクトリにOpenCVのAARファイルがあることを確認
- `build.gradle.kts` の依存関係設定を確認

**NDKエラー:**
- Android StudioのSDK Managerから最新のNDKをインストール

### 実行時エラー

**カメラが起動しない:**
- カメラ権限が許可されているか確認
- 他のアプリがカメラを使用していないか確認

**ボードが検出されない:**
- 照明を改善
- カメラのフォーカスを調整
- ボードとカメラの距離を調整（20-50cm推奨）
- ボードのサイズ設定が実際のボードと一致しているか確認

**精度が低い:**
- キャリブレーションをやり直す
- より多くのサンプルを収集
- カメラを固定して測定
- ボードの平坦性を確認

### データ保存エラー

**ファイルが保存されない:**
- ストレージ権限を確認（Android 10以降は不要）
- 十分なストレージ容量があるか確認

## 高精度化のためのヒント

### 1. ハードウェア
- 高解像度カメラ搭載の端末を使用
- カメラレンズをきれいに保つ
- 均一な照明を確保
- 高品質なChArUcoボード

### 2. キャリブレーション
- 50フレーム以上を収集（推奨）
- ボードを様々な角度・距離で撮影
- 画面全体を使ってボードを移動
- 再投影誤差が0.5ピクセル以下を目標

### 3. 測定時
- スポット測定では50-100サンプルを推奨
- カメラと端末をしっかり固定
- 十分な数のコーナーが検出されていることを確認（quality > 0.8）
- 標準偏差を確認（0.1mm以下が理想）

### 4. 環境
- 振動の少ない環境
- 安定した照明
- ChArUcoボードの反射を避ける
- 適切な距離（20-50cm）

## 開発情報

### デバッグビルド

```bash
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

### ログ確認

```bash
adb logcat -s CharucoTracking
```

### プロファイリング

Android StudioのProfilerを使用してパフォーマンスを確認できます。

## Python版との違い

- GUI表示のみ（CLIなし）
- ボード画像生成機能はPython版を使用
- 軌跡の可視化機能はPython版を使用
- 比較機能は未実装（Python版を使用）

## ライセンス

MIT License

## 参考文献

- OpenCV ArUco module documentation
- CameraX documentation
- "Automatic generation and detection of highly reliable fiducial markers under occlusion" (Garrido-Jurado et al., 2014)
