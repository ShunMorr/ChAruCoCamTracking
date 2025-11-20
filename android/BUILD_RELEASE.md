# APKビルドとリリース手順

このドキュメントでは、インストール可能なAPKをビルドしてGitHub Releaseで配布する手順を説明します。

## 前提条件

- Android Studio または JDK 17以上
- Android SDK (Android Studio経由でインストール可能)

## ステップ1: 署名鍵の作成

リリース用のAPKには署名が必要です。以下のコマンドで署名鍵を作成します：

```bash
# 署名鍵を作成（初回のみ）
keytool -genkey -v -keystore android/app/charuco-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias charuco-key
```

プロンプトに従って以下の情報を入力：
- パスワード（2回）
- 名前、組織名、市区町村、都道府県、国コード
- エイリアスのパスワード（keystore全体のパスワードと同じでOK）

**重要**:
- 作成した `.jks` ファイルとパスワードは安全に保管してください
- `.jks` ファイルは `.gitignore` に追加してGitにコミットしないでください

## ステップ2: 署名設定の追加

### 2.1 keystore.propertiesファイルの作成

```bash
cat > android/keystore.properties << 'EOF'
storePassword=YOUR_KEYSTORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=charuco-key
storeFile=charuco-release-key.jks
EOF
```

**YOUR_KEYSTORE_PASSWORD** と **YOUR_KEY_PASSWORD** を実際のパスワードに置き換えてください。

### 2.2 .gitignoreに追加

```bash
echo "keystore.properties" >> android/.gitignore
echo "*.jks" >> android/.gitignore
```

## ステップ3: デバッグAPKのビルド（テスト用）

署名なしのデバッグAPKを先にビルドしてテストできます：

```bash
cd android
./gradlew assembleDebug
```

生成されたAPK:
- `app/build/outputs/apk/debug/app-debug.apk`

インストール:
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## ステップ4: リリースAPKのビルド

署名済みのリリースAPKをビルドします：

```bash
cd android
./gradlew assembleRelease
```

生成されたAPK:
- `app/build/outputs/apk/release/app-release.apk`

## ステップ5: APKのテスト

```bash
# インストール
adb install app/build/outputs/apk/release/app-release.apk

# または実機でファイルマネージャーから直接インストール
```

## ステップ6: GitHub Releaseへの添付

1. GitHubのリポジトリページにアクセス
2. Releasesセクションに移動
3. 対象のリリースを編集
4. "Attach binaries by dropping them here or selecting them" の部分にAPKをドラッグ＆ドロップ
5. "Update release" をクリック

または新規リリース作成時に：
1. "Draft a new release" をクリック
2. タグやタイトル、説明を入力
3. APKファイルをドラッグ＆ドロップ
4. "Publish release" をクリック

## ステップ7: ユーザー向けインストール手順

リリースページに以下の手順を追加：

```markdown
## インストール方法

### Android端末での直接インストール

1. Assets欄から `app-release.apk` をダウンロード
2. Androidの設定で「不明なソースからのインストール」を許可
   - 設定 > セキュリティ > 不明なソースからのアプリ
3. ダウンロードしたAPKファイルをタップしてインストール

### 注意事項

- 初回インストール時、Androidが警告を表示する場合があります
- これは通常の動作です（Google Play経由ではないため）
- カメラ権限を許可してください

### 動作確認済み環境

- Android 7.0以上
- カメラ搭載端末
```

## APKサイズの最適化（オプション）

リリースAPKのサイズを削減するには：

1. ProGuardを有効化（build.gradle.ktsで設定済み）
2. 不要なリソースを削除
3. 使用していないライブラリを削除

## トラブルシューティング

### ビルドエラー

**OpenCVが見つからない:**
- `build.gradle.kts` でMaven経由のOpenCVを使用しているか確認
- インターネット接続を確認

**署名エラー:**
- `keystore.properties` のパスとパスワードを確認
- `.jks` ファイルが正しい場所にあるか確認

### インストールエラー

**"アプリをインストールできませんでした":**
- 不明なソースからのインストールを許可
- 既存のアプリをアンインストールしてから再インストール

**"パッケージの解析中にエラーが発生しました":**
- APKファイルが破損していないか確認
- Android OSのバージョンを確認（7.0以上が必要）
