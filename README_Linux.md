# Linux環境でのシラバススクレイピング実行手順

## 前提条件

1. **Python 3.8以上**がインストールされていること
2. **Chromeブラウザ**がインストールされていること
3. **pip**が利用可能であること

## セットアップ手順

### 1. 依存関係のインストール

```bash
# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 必要なパッケージをインストール
pip install -r requirements.txt
```

### 2. ChromeDriverの準備

#### 自動インストール（推奨）
`webdriver-manager`がインストールされていれば、スクリプトが自動的にChromeDriverをダウンロードします。

#### 手動インストール
1. [ChromeDriver公式サイト](https://chromedriver.chromium.org/)からChromeDriverをダウンロード
2. ダウンロードしたファイルを解凍
3. 以下のコマンドでインストール：

```bash
# ChromeDriverを/usr/local/bin/に移動
sudo mv chromedriver /usr/local/bin/

# 実行権限を付与
sudo chmod +x /usr/local/bin/chromedriver

# パスが通っているか確認
which chromedriver
```

### 3. 実行

```bash
# 仮想環境をアクティベート（まだの場合）
source venv/bin/activate

# スクリプトを実行
python3 unipa.py
```

## トラブルシューティング

### ChromeDriverが見つからない場合

```bash
# ChromeDriverのバージョンを確認
chromedriver --version

# Chromeブラウザのバージョンを確認
google-chrome --version

# バージョンが一致しない場合は、ChromeDriverを再ダウンロード
```

### 権限エラーが発生する場合

```bash
# ChromeDriverに実行権限を付与
sudo chmod +x /usr/local/bin/chromedriver

# または、現在のディレクトリのChromeDriverに権限を付与
chmod +x ./chromedriver
```

### メモリ不足エラーが発生する場合

スクリプトは既にメモリ使用量を最適化していますが、システムのメモリが不足している場合は：

```bash
# 他のプロセスを終了
# または、ヘッドレスモードで実行（スクリプトが自動的に試行します）
```

### ネットワークエラーが発生する場合

```bash
# インターネット接続を確認
ping google.com

# プロキシ設定が必要な場合は、環境変数を設定
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

## 出力ファイル

実行が完了すると、以下のファイルが生成されます：

- `syllabus_results_basic.csv`: 基本情報のデータ
- `syllabus_results_detailed.csv`: 詳細情報のデータ

## 注意事項

1. **実行時間**: 全曜日のデータを取得するため、数時間かかる場合があります
2. **ネットワーク負荷**: 大量のリクエストを送信するため、ネットワークに負荷がかかります
3. **ブラウザの安定性**: 長時間の実行によりブラウザが不安定になる場合があります

## ログの確認

スクリプト実行中は詳細なログが出力されます。エラーが発生した場合は、ログを確認して問題を特定してください。 