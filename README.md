# このリポジトリについて
コイツは岡山理科大学のポータルサイト（通称:マイログ）からシラバスをスクレイピングしてくるスクリプトです。
Seleniumでゴリ押しで動かしてます。

# 実行方法

このリポジトリをクローンして

```
git clone https://github.com/tm20314/Mylog-Scrapar.git
```

該当ディレクトリに移動して
```
cd hogegoge/Mylog-Scrapar
```
seleniumをインストールし
```
pip install selenium
```
実行してください。
```
python -u "/hogehoge/Mylog-Scrapar/unipa.py"
```


実行中は以下のような動作となります。完了すると自動的にChromeが終了し、ディレクトリ内部に「syllabus_results_all_days」というCSVファイルが生成されます。

[![text](https://img.youtube.com/vi/O5cupaiInXY/0.jpg)](https://youtu.be/O5cupaiInXY)


