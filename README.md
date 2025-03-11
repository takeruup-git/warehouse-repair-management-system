# 倉庫修繕費管理システム (Warehouse Repair Management System)

倉庫会社向けの修繕費管理アプリケーションです。フォークリフト、倉庫施設、昇降機などの資産の修繕履歴を追跡し、メンテナンススケジュールを予測し、点検報告書を管理します。

## 機能

- ダッシュボード：月別修繕費推移グラフ、修繕費上位車両、交換・点検アラート
- 資産管理：フォークリフト、倉庫施設、昇降機の詳細情報管理
- 修繕履歴：修繕日、費用、理由、業者などの記録
- 点検報告書：バッテリー液量点検表、定期自主検査記録表、始業前点検報告書
- レポート生成：月別修繕費、車両別修繕履歴、修繕対象種別実績一覧、倉庫別修繕履歴
- 予算管理：資産種別ごとの年間修繕費予算設定と実績比較
- データインポート/エクスポート：Excel/CSVファイルの入出力

## 技術スタック

- バックエンド: Python 3.9+ / Flask 2.3.2
- データベース: SQLite / SQLAlchemy 2.0.20
- フロントエンド: HTML / CSS / JavaScript / Bootstrap 5
- レポート生成: pandas 2.1.0 / reportlab 4.0.4

## セットアップ手順 (Windows環境)

### 前提条件

- Python 3.9以上がインストールされていること
- pipがインストールされていること

### インストール手順

1. リポジトリをクローンまたはダウンロードする

```
git clone https://github.com/yourusername/warehouse-repair-management-system.git
cd warehouse-repair-management-system
```

2. 仮想環境を作成して有効化する（推奨）

```
python -m venv venv
venv\Scripts\activate
```

3. 必要なパッケージをインストールする

```
pip install -r requirements.txt
```

4. データベースを初期化する

```
python init_db.py
```

5. サンプルデータを追加する（オプション）

```
python add_sample_data.py
```

6. アプリケーションを起動する

```
python app.py
```

7. ブラウザで以下のURLにアクセスする

```
http://localhost:5000
```

ローカルネットワーク内の他のコンピュータからアクセスするには、IPアドレスを使用します：

```
http://[あなたのIPアドレス]:5000
```

## ディレクトリ構造

```
warehouse-repair-management-system/
├── app/
│   ├── models/          # データベースモデル
│   ├── routes/          # ルート定義
│   ├── static/          # 静的ファイル（CSS、JS、アップロードファイル）
│   ├── templates/       # HTMLテンプレート
│   └── utils/           # ユーティリティ関数
├── migrations/          # データベースマイグレーション
├── uploads/             # アップロードされたファイルの保存先
├── app.py               # アプリケーションのエントリーポイント
├── config.py            # 設定ファイル
├── init_db.py           # データベース初期化スクリプト
├── add_sample_data.py   # サンプルデータ追加スクリプト
├── requirements.txt     # 依存パッケージリスト
└── README.md            # このファイル
```

## 使用方法

1. ダッシュボード画面から全体の状況を確認
2. 「資産一覧」から資産の詳細情報を閲覧・編集
3. 「修繕履歴」から修繕記録を追加・編集
4. 「点検報告書」から各種点検表を作成・出力
5. 「レポート」から各種レポートを生成・出力

## サンプルデータ

以下のサンプルデータが含まれています：

- フォークリフト：5台（リーチ式/カウンター式、バッテリー/軽油の組み合わせ）
- 倉庫：2箇所
- 修繕履歴：10件（アワーメーター値付き）

## ライセンス

[MIT License](LICENSE)