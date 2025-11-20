# APKビルド クイックチェックリスト

このチェックリストを使って、環境が正しくセットアップされているか確認できます。

## ✅ 環境確認チェックリスト

### ステップ1: JDKの確認

```bash
java -version
```

✅ `openjdk version "17.0.x"` または `"21.0.x"` と表示される
❌ エラーが出る → [SETUP_ENVIRONMENT.md](SETUP_ENVIRONMENT.md) のJDKインストール手順を参照

### ステップ2: Android SDKの確認

```bash
adb --version
```

✅ `Android Debug Bridge version x.x.x` と表示される
❌ エラーが出る → Android SDKのインストールが必要

```bash
echo $ANDROID_HOME   # Linux/macOS
echo %ANDROID_HOME%  # Windows
```

✅ Android SDKのパスが表示される（例: `/Users/username/Android` または `C:\Android`）
❌ 何も表示されない → 環境変数の設定が必要

### ステップ3: Gradleの確認

```bash
cd android
./gradlew --version   # Linux/macOS
.\gradlew --version   # Windows
```

✅ Gradleのバージョン情報が表示される
❌ `Permission denied` → `chmod +x gradlew` を実行
❌ その他のエラー → JDKまたはAndroid SDKの設定を確認

## 🔨 ビルド手順

### デバッグAPKのビルド（テスト用）

```bash
cd android
./gradlew assembleDebug
```

**生成場所**: `app/build/outputs/apk/debug/app-debug.apk`

**所要時間**: 初回5-10分、2回目以降1-2分

### リリースAPKのビルド（配布用）

#### 1回目（署名鍵の作成が必要）

```bash
# 署名鍵を作成
keytool -genkey -v -keystore app/charuco-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias charuco-key

# 情報を入力（パスワードは忘れないように！）
```

```bash
# keystore.propertiesを作成
cat > keystore.properties << 'EOF'
storePassword=YOUR_PASSWORD_HERE
keyPassword=YOUR_PASSWORD_HERE
keyAlias=charuco-key
storeFile=app/charuco-release-key.jks
EOF
```

⚠️ `YOUR_PASSWORD_HERE` を実際のパスワードに置き換えてください

```bash
# ビルド
./build-release.sh
```

#### 2回目以降（署名鍵作成済み）

```bash
./build-release.sh
```

**生成場所**: `app/build/outputs/apk/release/app-release.apk`

## 📱 APKのインストール

### Android端末にUSB接続してインストール

```bash
# USBデバッグを有効にした端末を接続

# 接続確認
adb devices

# インストール
adb install app/build/outputs/apk/debug/app-debug.apk
```

### ファイル転送でインストール

1. APKファイルをAndroid端末に転送（USB、メール、クラウドなど）
2. Android端末で「不明なソースからのインストール」を許可
3. APKファイルをタップしてインストール

## 🚀 GitHub Releaseへのアップロード

1. **APKをビルド**:
   ```bash
   ./build-release.sh
   ```

2. **GitHubのReleaseページにアクセス**:
   - https://github.com/ShunMorr/ChAruCoCamTracking/releases

3. **新規リリースを作成または既存リリースを編集**

4. **APKをアップロード**:
   - `app/build/outputs/apk/release/app-release.apk` をドラッグ＆ドロップ

5. **リリースノートに追記**:
   ```markdown
   ## ダウンロード

   📱 **app-release.apk** - Android 7.0以上で動作

   ### インストール方法
   1. APKをダウンロード
   2. 「不明なソースからのインストール」を許可
   3. APKをタップしてインストール
   ```

## 🐛 よくあるエラーと解決方法

### `JAVA_HOME is not set`

**原因**: JDKがインストールされていないか、環境変数が設定されていない

**解決方法**:
```bash
# macOS
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

# Linux
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Windows（システム環境変数で設定）
# JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-17.0.x
```

### `SDK location not found`

**原因**: Android SDKがインストールされていないか、ANDROID_HOMEが設定されていない

**解決方法**:
```bash
# Linux/macOS
export ANDROID_HOME=$HOME/Android

# Windows（システム環境変数で設定）
# ANDROID_HOME = C:\Android
```

### `Execution failed for task ':app:mergeDebugResources'`

**原因**: Gradleキャッシュの問題

**解決方法**:
```bash
./gradlew clean
./gradlew assembleDebug
```

### `Unable to resolve dependency`

**原因**: インターネット接続の問題またはプロキシ設定

**解決方法**:
1. インターネット接続を確認
2. ファイアウォール設定を確認
3. 企業ネットワークの場合、プロキシ設定が必要な場合があります

### ビルドが遅い

**最適化方法**:
1. Gradleデーモンを有効化（デフォルトで有効）
2. メモリを増やす: `gradle.properties` に以下を追加
   ```
   org.gradle.jvmargs=-Xmx4096m
   ```
3. 並列ビルドを有効化: `gradle.properties` に以下を追加
   ```
   org.gradle.parallel=true
   ```

## 📋 推奨ワークフロー

### 初回セットアップ（1回のみ）

1. ✅ JDKインストール
2. ✅ Android SDKインストール
3. ✅ 環境変数設定
4. ✅ デバッグAPKでビルドテスト

### 配布用APK作成（初回）

1. ✅ 署名鍵作成
2. ✅ keystore.properties作成
3. ✅ リリースAPKビルド
4. ✅ 動作テスト
5. ✅ GitHub Releaseにアップロード

### 更新版の配布（2回目以降）

1. ✅ コード変更
2. ✅ バージョン番号更新（`build.gradle.kts`の`versionCode`と`versionName`）
3. ✅ `./build-release.sh`
4. ✅ 動作テスト
5. ✅ GitHub Releaseにアップロード

## 🎯 ゴール

このチェックリストを完了すると：

✅ デバッグAPKをビルドできる
✅ リリースAPKをビルドできる
✅ GitHub Releaseで配布できる
✅ ユーザーがダウンロードしてそのままインストールできる

---

質問がある場合は [SETUP_ENVIRONMENT.md](SETUP_ENVIRONMENT.md) の詳細ガイドを参照してください。
