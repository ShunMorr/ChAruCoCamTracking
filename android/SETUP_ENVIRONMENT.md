# Android APKビルド環境のセットアップ

AndroidアプリをビルドするためのPC環境セットアップガイドです。

## 必要なもの

### 1. JDK (Java Development Kit)
- **バージョン**: JDK 17以上（推奨: JDK 17またはJDK 21）
- **用途**: Gradleとビルドツールの実行

### 2. Android SDK
- **コマンドラインツール**または**Android Studio**経由でインストール
- **必要なコンポーネント**:
  - Android SDK Platform (API 34)
  - Android SDK Build-Tools
  - Android SDK Platform-Tools

### 3. Gradle
- プロジェクトに`gradlew`（Gradle Wrapper）が含まれているため、別途インストール不要

---

## オプション1: VS Codeでビルド（軽量・推奨）

VS Codeとコマンドラインツールを使用する方法です。

### ステップ1: JDKのインストール

#### Windows
```powershell
# Chocolateyを使用
choco install openjdk17

# または公式サイトからダウンロード
# https://adoptium.net/
```

#### macOS
```bash
# Homebrewを使用
brew install openjdk@17

# パスを設定
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install openjdk-17-jdk
```

**確認**:
```bash
java -version
# openjdk version "17.0.x" と表示されればOK
```

### ステップ2: Android SDK（コマンドラインツール）のインストール

#### 方法A: Android SDK Command-line Toolsを使用（推奨）

1. **ダウンロード**:
   - https://developer.android.com/studio#command-line-tools-only
   - 「Command line tools only」をダウンロード

2. **展開**:
   ```bash
   # Linux/macOS
   mkdir -p ~/Android/cmdline-tools
   unzip commandlinetools-*.zip -d ~/Android/cmdline-tools
   mv ~/Android/cmdline-tools/cmdline-tools ~/Android/cmdline-tools/latest

   # Windows
   # C:\Android\cmdline-tools\latest に展開
   ```

3. **環境変数を設定**:

   **Linux/macOS** (`~/.bashrc` または `~/.zshrc` に追加):
   ```bash
   export ANDROID_HOME=$HOME/Android
   export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   ```

   **Windows** (環境変数を設定):
   ```
   ANDROID_HOME=C:\Android
   Path に追加:
     %ANDROID_HOME%\cmdline-tools\latest\bin
     %ANDROID_HOME%\platform-tools
   ```

4. **SDK パッケージをインストール**:
   ```bash
   # ライセンスに同意
   sdkmanager --licenses

   # 必要なパッケージをインストール
   sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
   ```

**確認**:
```bash
adb --version
# Android Debug Bridge version x.x.x と表示されればOK
```

### ステップ3: VS Codeの設定

1. **VS Codeをインストール**:
   - https://code.visualstudio.com/

2. **拡張機能をインストール（オプション）**:
   - `Kotlin Language` - Kotlinのシンタックスハイライト
   - `Gradle for Java` - Gradleタスクの実行
   - `Android iOS Emulator` - エミュレータ操作

3. **プロジェクトを開く**:
   ```bash
   cd ChAruCoCamTracking/android
   code .
   ```

### ステップ4: ビルドとインストール

VS Codeの統合ターミナルで実行:

```bash
# デバッグAPKをビルド
./gradlew assembleDebug

# リリースAPKをビルド（署名鍵設定後）
./build-release.sh

# 接続されたAndroid端末にインストール
./gradlew installDebug
```

---

## オプション2: Android Studioでビルド（フル機能）

Android Studioは統合された開発環境で、エミュレータやデバッガも含まれます。

### ステップ1: Android Studioのインストール

1. **ダウンロード**:
   - https://developer.android.com/studio

2. **インストール**:
   - インストーラーを実行
   - セットアップウィザードに従う
   - Android SDK、AVD（エミュレータ）も自動インストール

### ステップ2: プロジェクトを開く

1. Android Studioを起動
2. `Open an Existing Project` を選択
3. `ChAruCoCamTracking/android` フォルダを選択
4. Gradleの同期を待つ

### ステップ3: ビルドとインストール

1. **ビルド**:
   - メニュー: `Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`

2. **インストール**:
   - メニュー: `Run` → `Run 'app'`
   - または再生ボタン（▶）をクリック

3. **APKの場所**:
   - 画面下部の通知から「locate」をクリック
   - または `app/build/outputs/apk/` フォルダを開く

---

## ビルドの手順（共通）

### 1. 初回ビルド（デバッグAPK）

署名なしでテスト用のAPKをビルド:

```bash
cd android
./gradlew assembleDebug
```

生成場所: `app/build/outputs/apk/debug/app-debug.apk`

### 2. リリースAPKのビルド

配布用の署名済みAPKをビルド:

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

生成場所: `app/build/outputs/apk/release/app-release.apk`

---

## トラブルシューティング

### ビルドエラー

#### `JAVA_HOME is not set`

JDKが正しくインストールされていません:

```bash
# JDKのインストール確認
java -version

# JAVA_HOMEを設定（Linux/macOS）
export JAVA_HOME=$(/usr/libexec/java_home -v 17)  # macOS
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64  # Linux

# Windows
# 環境変数で JAVA_HOME を設定
# 例: C:\Program Files\Eclipse Adoptium\jdk-17.0.x
```

#### `Android SDK not found`

Android SDKが正しくインストールされていません:

```bash
# ANDROID_HOMEを確認
echo $ANDROID_HOME

# 設定されていない場合
export ANDROID_HOME=$HOME/Android  # Linux/macOS
# または環境変数で ANDROID_HOME を設定（Windows）
```

#### `Execution failed for task ':app:mergeDebugResources'`

Gradleキャッシュをクリア:

```bash
./gradlew clean
./gradlew assembleDebug
```

#### `OpenCV not found`

インターネット接続を確認してください。OpenCVはMaven経由で自動ダウンロードされます。

### Gradle関連

#### Gradleバージョンエラー

Gradle Wrapperを更新:

```bash
./gradlew wrapper --gradle-version=8.5
```

#### Permission denied (Linux/macOS)

`gradlew`に実行権限を付与:

```bash
chmod +x gradlew
```

### APKインストールエラー

#### `INSTALL_FAILED_UPDATE_INCOMPATIBLE`

既存のアプリをアンインストールしてから再インストール:

```bash
adb uninstall com.charuco.tracking
adb install app/build/outputs/apk/debug/app-debug.apk
```

#### `adb: device offline`

端末を再接続:

```bash
adb kill-server
adb start-server
adb devices
```

---

## 推奨環境

### 最小要件
- **CPU**: 2コア以上
- **RAM**: 8GB以上
- **ストレージ**: 10GB以上の空き容量

### 推奨環境
- **CPU**: 4コア以上
- **RAM**: 16GB以上
- **ストレージ**: SSD、20GB以上の空き容量

---

## まとめ

### VS Code + コマンドライン（軽量）

**メリット**:
- 軽量で高速
- 他の開発にも使える
- ディスク容量が少ない（約2-3GB）

**デメリット**:
- UIがない
- エミュレータが含まれない
- デバッグが手動

**推奨**: ビルドのみが目的の場合

### Android Studio（フル機能）

**メリット**:
- 統合環境
- ビジュアルエディタ
- エミュレータ内蔵
- デバッガ完備

**デメリット**:
- 重い
- ディスク容量が大きい（約10-15GB）
- 起動が遅い

**推奨**: アプリ開発を継続する場合

---

## クイックスタート（最短手順）

### Windows
```powershell
# JDKをインストール
choco install openjdk17

# Android Command-line Toolsをダウンロード・展開
# https://developer.android.com/studio#command-line-tools-only

# 環境変数を設定（システム設定から）
# ANDROID_HOME=C:\Android

# SDKをインストール
sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

# ビルド
cd ChAruCoCamTracking\android
.\gradlew assembleDebug
```

### macOS/Linux
```bash
# JDKをインストール
# macOS: brew install openjdk@17
# Linux: sudo apt install openjdk-17-jdk

# Android Command-line Toolsをダウンロード・展開
wget https://dl.google.com/android/repository/commandlinetools-linux-*.zip
mkdir -p ~/Android/cmdline-tools
unzip commandlinetools-*.zip -d ~/Android/cmdline-tools
mv ~/Android/cmdline-tools/cmdline-tools ~/Android/cmdline-tools/latest

# 環境変数を設定
export ANDROID_HOME=$HOME/Android
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# SDKをインストール
sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

# ビルド
cd ChAruCoCamTracking/android
./gradlew assembleDebug
```

---

質問や問題が発生した場合は、GitHubのIssuesで報告してください。
