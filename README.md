# syuwatto-translator

![Static Badge](https://img.shields.io/badge/Sony-Spresense-blue)

## 製品について
本製品は指文字を用いた円滑なコミュニケーションを助けるデバイスである。

![製品](./images/product1.png)

## レポジトリの構成
・hardware ： 3Dモデルや配線、パーツリスト等のハード設計に関するデータ

・spresense ： SPRESENSEに書き込むプログラム

・server ： server用のプログラム

## ビルド
1.SPRESENSEのArduinoプロジェクトがビルドできる状態にします(詳細はSonyのSPRESENSE公式ページをご覧ください)。

2.ArudinoIDEで~/syuwatto-translator/spresense/program/WebCameraにあるWebCamera.inoを開いてください。

3.~/syuwatto-translator/spresense/program/WebCameraにあるconfig.h内の「AP_SSID」「PASSPHRASE」「SERVER_IP」「SERVER_PORT」をそれぞれ指定してください。

4.SPRESENSEをPCに接続します。

5.WebCamera.inoをマイコンに書き込みます。

## センサーについて
この製品を扱うにあたって、SPRESENSEとセンサーの接続は以下の画像を参考にしてください。

![接続](./images/image1.png)

また、仕様書?パーツリスト？は以下の通りになります。

![仕様](./images/image2.png)

## 使い方

## クラウド(サーバー)側使い方
サーバ側の処理はubuntuがインストールされたPCでの動作を想定している。

### このリポジトリのクローン
このリポジトリを自身のホームディレクトリにクローンする。
```sh
$ cd ~/
$ git clone https://github.com/rsdlab/syuwatto-translator.git
```

### Dockerイメージの作成
以下のコマンドにてDockerのビルドを行う。
```sh
$ cd ~/syuwatto-translator/server/docker
$ ./build.sh
```

### Dockerコンテナの起動
ビルドが終了したら、以下のコマンドにてDockerコンテナを起動する。
```sh
$ ./run.sh
```

### ネットワークの接続
本デバイスを接続するネットワークにサーバとして使用するPCを接続する。

### IPアドレス等の設定
~/syuwatto-translator/server/shared_dir/server.py内のIPとPORTを自身の環境に応じて設定する。

### サーバの起動
以下のコマンドにてサーバを起動する。
```sh
$ python3 server.py
```

## 機能
本製品の機能は以下の通りです。

・指文字から音声への翻訳

・音声からテキストへの翻訳

・指文字の練習機能

詳しくは以下の動画をご覧ください

[![movie1](./images/backcolor.png)](https://github.com/rsdlab/syuwatto-translator/assets/105686812/fd62dd02-c0c1-43e5-8c7f-474890054772)

## システムモデル

本製品のシステム構成のイメージ図は以下の通りです。

![system](./images/system.png)

## Contributors
Satoshi Kikuchi ([m-SKikuchi](https://github.com/m-SKikuchi))<br>
Kazuya Yabashi ([yakazuya](https://github.com/yakazuya))<br>
Masatomo Inoue ([InoueMasatomo](https://github.com/InoueMasatomo))<br>
AyatoTakagi ([tadrone](https://github.com/tadrone))

## Contacts
If you have further question, email to 233427037@ccmailg.meijo-u.ac.jp