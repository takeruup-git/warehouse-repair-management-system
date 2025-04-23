# 倉庫修繕費管理システム (Warehouse Repair Management System)

倉庫会社向けの修繕費管理アプリケーションです。フォークリフト、倉庫施設、昇降機などの資産の修繕履歴を追跡し、メンテナンススケジュールを予測し、点検報告書を管理します。

## 機能

- ユーザー認証：ログイン/ログアウト、権限管理（一般ユーザー、管理者、システム管理者）
- ダッシュボード：月別修繕費推移グラフ、修繕費上位車両、交換・点検アラート
- 資産管理：フォークリフト、倉庫施設、昇降機の詳細情報管理
- 修繕履歴：修繕日、費用、理由、業者などの記録
- 点検報告書：バッテリー液量点検表、定期自主検査記録表、始業前点検報告書
- レポート生成：月別修繕費、車両別修繕履歴、修繕対象種別実績一覧、倉庫別修繕履歴
- 予算管理：資産種別ごとの年間修繕費予算設定と実績比較
- データインポート/エクスポート：Excel/CSVファイルの入出力
- PDF管理：点検報告書や修繕報告書のPDF生成、アップロード、閲覧、ダウンロード、検索
- 年次点検機能：フォークリフトの年次点検記録管理と報告書生成
- 操作者管理：システム操作者の登録・管理と操作履歴の記録
- 統合テスト：自動化されたテストフレームワークによる機能検証

## 技術スタック

- バックエンド: Python 3.12+ / Flask 2.3.2
- データベース: SQLite / SQLAlchemy 2.0.20
- フロントエンド: HTML / CSS / JavaScript / Bootstrap 5
- レポート生成: pandas 2.0+ / reportlab 4.0.4
- PDF管理: reportlab 4.0.4 / Pillow 10.0.0
- Excel操作: openpyxl 3.1.2 / xlsxwriter 3.1.0
- テスト: pytest 7.4.0 / pytest-flask 1.2.0 / pytest-cov 4.1.0 / selenium 4.11.2
- ユーザー認証: Flask-Login 0.6.2 / Flask-Session 0.5.0
- フォーム処理: Flask-WTF 1.1.1 / WTForms 3.0.1
- デプロイ: gunicorn 21.2.0

## セットアップ手順

### 前提条件

- Python 3.12以上がインストールされていること
- pipがインストールされていること

### インストール手順

1. リポジトリをクローンまたはダウンロードする

```bash
git clone https://github.com/takeruup-git/warehouse-repair-management-system.git
cd warehouse-repair-management-system
```

2. 仮想環境を作成して有効化する（推奨）

#### Windows環境
```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/Mac環境
```bash
python -m venv venv
source venv/bin/activate
```

3. 必要なパッケージをインストールする

```bash
pip install -r requirements.txt
```

4. データベースを初期化する

```bash
python init_db.py
```

5. データベースマイグレーションを適用する

#### Linux/Mac環境
```bash
python -m flask db upgrade
```

#### Windows環境
Windows環境では、以下の手順でマイグレーションを適用してください：

```bash
# 環境変数を設定
set FLASK_APP=app.py

# マイグレーションを実行
python -m flask db upgrade
```

もし `Error: No such command 'db'` というエラーが表示される場合は、Flask-Migrateが正しくインストールされていない可能性があります。以下のコマンドで再インストールしてください：

```bash
pip install flask-migrate
set FLASK_APP=app.py
python -m flask db upgrade
```

それでも問題が解決しない場合や、マイグレーションでエラーが発生した場合（"Can't locate revision identified by 'acbca60fe487'"など）は、以下の修正スクリプトを実行してください：

```bash
python fix_migration.py
```

このスクリプトは、マイグレーションの問題を修正し、不足しているテーブルを作成します。

6. 初期管理者ユーザーを作成する

```bash
python add_admin_user.py admin admin@example.com password123
```

7. サンプルデータを追加する（オプション）

```bash
python add_sample_data.py
```

8. アプリケーションを起動する

```bash
python app.py
```

9. ブラウザで以下のURLにアクセスする

```
http://localhost:51873
```

10. 作成した管理者ユーザーでログインする

```
ユーザー名: admin
パスワード: password123
```

ローカルネットワーク内の他のコンピュータからアクセスするには、IPアドレスを使用します：

```
http://[あなたのIPアドレス]:51873
```

## ディレクトリ構造

```
warehouse-repair-management-system/
├── app/
│   ├── forms/           # フォーム定義
│   ├── models/          # データベースモデル
│   ├── routes/          # ルート定義
│   │   ├── annual_inspection.py  # 年次点検機能
│   │   ├── operator.py           # 操作者管理機能
│   │   └── pdf.py                # PDF管理機能
│   ├── static/          # 静的ファイル（CSS、JS、アップロードファイル）
│   │   └── uploads/     # アップロードされたファイル
│   │       └── pdf/     # PDFファイル保存先
│   ├── templates/       # HTMLテンプレート
│   │   ├── annual_inspection/    # 年次点検関連テンプレート
│   │   ├── operator/             # 操作者管理関連テンプレート
│   │   └── pdf/                  # PDF管理関連テンプレート
│   └── utils/           # ユーティリティ関数
├── docs/                # ドキュメント
│   └── integration_test.md  # 統合テスト説明
├── migrations/          # データベースマイグレーション
├── tests/               # テストコード
│   ├── integration/     # 統合テスト
│   └── uploads/         # テスト用アップロードディレクトリ
├── app.py               # アプリケーションのエントリーポイント
├── config.py            # 設定ファイル
├── init_db.py           # データベース初期化スクリプト
├── add_sample_data.py   # サンプルデータ追加スクリプト
├── add_admin_user.py    # 管理者ユーザー作成スクリプト
├── pdf_management.md    # PDF管理機能説明
├── pytest.ini           # pytestの設定ファイル
├── requirements.txt     # 依存パッケージリスト
├── run_integration_tests.py  # 統合テスト実行スクリプト
└── README.md            # このファイル
```

## 使用方法

1. 管理者ユーザーでログイン
2. 操作者を選択または新規登録
3. ダッシュボード画面から全体の状況を確認
4. 「資産一覧」から資産の詳細情報を閲覧・編集
5. 「修繕履歴」から修繕記録を追加・編集
6. 「点検報告書」から各種点検表を作成・出力
7. 「年次点検」からフォークリフトの年次点検記録を管理
8. 「PDF管理」から点検報告書や修繕報告書のPDFを管理
9. 「レポート」から各種レポートを生成・出力
10. CSVファイルからデータをインポート/エクスポート
11. 管理者は「ユーザー管理」からユーザーの追加・編集・削除が可能
12. 「操作者管理」から操作者情報を管理

## サンプルデータ

以下のサンプルデータが含まれています：

- フォークリフト：5台（リーチ式/カウンター式、バッテリー/軽油の組み合わせ）
- 倉庫：2箇所
- 修繕履歴：10件（アワーメーター値付き）
- 年次点検記録：3件
- 操作者：5名
- PDFファイル：点検報告書、修繕報告書のサンプル

## テスト実行

統合テストは以下のコマンドで実行できます：

```bash
# すべての統合テストを実行
python run_integration_tests.py

# 特定のテストのみ実行
pytest -xvs tests/integration/test_csv_upload.py
```

テストの詳細については、[統合テストドキュメント](docs/integration_test.md)を参照してください。

## PDF管理機能

PDF管理機能の詳細については、[PDF管理ドキュメント](pdf_management.md)を参照してください。

## ライセンス

[MIT License](LICENSE)

## 動作環境

- OS: Windows 10/11, macOS, Linux
- ブラウザ: Chrome, Firefox, Edge (最新版推奨)
- メモリ: 4GB以上推奨
- ディスク容量: 500MB以上の空き容量

## 更新履歴

- 2025-04-23: READMEを更新、Python 3.12対応を明記、ポート番号を修正