
#!/bin/bash

# スクリプトのディレクトリに移動
cd ~/mylog-scraper

# 仮想環境をアクティベート
source venv/bin/activate

# Pythonスクリプトを実行
python3 unipa.py

# 仮想環境をデアクティベート
deactivate 