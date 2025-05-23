# 倉庫修繕費管理システム (Warehouse Repair Management System)

倉庫会社向けの修繕費管理アプリケーションです。フォークリフト、倉庫施設などの資産の修繕履歴を追跡し、メンテナンススケジュールを予測し、点検報告書を管理します。

## 機能

- ユーザー認証：ログイン/ログアウト、権限管理（一般ユーザー、管理者、システム管理者）
- ダッシュボード：月別修繕費推移グラフ、修繕費上位車両、交換・点検アラート
- 資産管理：フォークリフト、倉庫施設の詳細情報管理
- 修繕履歴：修繕日、費用、理由、業者などの記録
- 点検報告書：バッテリー液量点検表、定期自主検査記録表、始業前点検報告書
- レポート生成：月別修繕費、車両別修繕履歴、修繕対象種別実績一覧、倉庫別修繕履歴
- データインポート/エクスポート：Excel/CSVファイルの入出力
- PDF管理：点検報告書や修繕報告書のPDF生成、アップロード、閲覧、ダウンロード、検索
- 年次点検機能：フォークリフトの年次点検記録管理と報告書生成
- 操作者管理：システム操作者の登録・管理
- 統合テスト：自動化されたテストフレームワークによる機能検証

## 技術スタック

- バックエンド: Python 3.9+ / Flask 2.3.2
- データベース: SQLite / SQLAlchemy 2.0.20
- フロントエンド: HTML / CSS / JavaScript / Bootstrap 5
- レポート生成: pandas 2.0+ / reportlab 4.0.4
- PDF管理: reportlab 4.0.4 / Pillow 10.0.0
- Excel操作: openpyxl 3.1.2 / xlsxwriter 3.1.0
- テスト: pytest 7.4.0 / pytest-flask 1.2.0 / pytest-cov 4.1.0
- ユーザー認証: Flask-Login 0.6.2 / Flask-Session 0.5.0
- フォーム処理: Flask-WTF 1.1.1 / WTForms 3.0.1

## セットアップ手順

### 前提条件

- Python 3.9以上がインストールされていること
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

#### 新しい統合マイグレーションスクリプトを使用する方法（推奨）

Windows環境とLinux/Mac環境の両方で動作する統合マイグレーションスクリプトを用意しました。以下のコマンドで実行できます：

```bash
# すべての環境で共通
python run_migration.py
```

#### Windows環境の場合は、バッチファイルも使用できます：

```bash
# Windowsのみ
run_migration_windows.bat
```

このスクリプトは以下の機能を提供します：
- 環境に応じた適切なコマンド実行
- データベース接続の確認と再試行
- マイグレーションエラーの自動修正
- 詳細なログ出力（migration.log）

詳細については、[Windows環境でのマイグレーション問題と解決策](docs/windows_migration.md)を参照してください。

#### 従来の方法（非推奨）

##### Linux/Mac環境
```bash
python -m flask db upgrade
```

##### Windows環境
```bash
# 環境変数を設定
set FLASK_APP=app.py

# マイグレーションを実行
python -m flask db upgrade
```

もし従来の方法でエラーが発生した場合は、以下の修正スクリプトを実行してください：

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
http://localhost:53319
```

10. 作成した管理者ユーザーでログインする

```
ユーザー名: admin
パスワード: password123
```

ローカルネットワーク内の他のコンピュータからアクセスするには、IPアドレスを使用します：

```
http://[あなたのIPアドレス]:53319
```

## Windows用インストーラーの作成

Windows環境でインストーラーを作成する手順は以下の通りです：

### 必要なツール

1. Python 3.8以上
2. PyInstaller
3. Inno Setup (Windows用インストーラー作成ツール)

### インストーラー作成手順

1. 必要なパッケージをインストール

```bash
pip install pyinstaller pywin32 winshell
```

2. アプリケーションをビルド

```bash
python build_windows_app.py
```

このコマンドは以下の処理を行います：
- PyInstallerを使用してアプリケーションをビルド
- 初回起動用と通常起動用のバッチファイルを作成
- Inno Setup用のスクリプトファイルを作成

3. Inno Setupを使用してインストーラーを作成

```bash
iscc 倉庫修繕費管理システム.iss
```

4. 作成されたインストーラー（`installer/倉庫修繕費管理システム_セットアップ.exe`）を配布

### インストール後の使用方法

1. インストール完了時に「初回セットアップを実行」オプションを選択するか、スタートメニューまたはデスクトップの「倉庫修繕費管理システム - 初回起動」ショートカットをクリック
2. 初回起動時に管理者ユーザーを作成し、必要に応じてサンプルデータを追加
3. 以降は、デスクトップの「倉庫修繕費管理システム」アイコンをクリックして起動

詳細な手順については、[Windows インストーラー作成手順](WINDOWS_INSTALLER_README.md)を参照してください。

## ディレクトリ構造

```
warehouse-repair-management-system/
├── app/
│   ├── forms/           # フォーム定義
│   ├── models/          # データベースモデル
│   ├── routes/          # ルート定義
│   │   ├── annual_inspection.py  # 年次点検機能
│   │   ├── api.py                # API機能
│   │   ├── auth.py               # 認証機能
│   │   ├── csv_upload.py         # CSVアップロード機能
│   │   ├── facility.py           # 倉庫施設管理機能
│   │   ├── forklift.py           # フォークリフト管理機能
│   │   ├── inspection.py         # 点検機能
│   │   ├── main.py               # メイン機能
│   │   ├── operator.py           # 操作者管理機能
│   │   ├── pdf_management.py     # PDF管理機能
│   │   ├── repair.py             # 修繕管理機能
│   │   └── report.py             # レポート機能
│   ├── static/          # 静的ファイル（CSS、JS、アップロードファイル）
│   │   ├── css/         # CSSファイル
│   │   ├── js/          # JavaScriptファイル
│   │   └── uploads/     # アップロードされたファイル
│   ├── templates/       # HTMLテンプレート
│   │   ├── annual_inspection/    # 年次点検関連テンプレート
│   │   ├── auth/                 # 認証関連テンプレート
│   │   ├── components/           # 共通コンポーネント
│   │   ├── csv_upload/           # CSVアップロード関連テンプレート
│   │   ├── errors/               # エラーページ
│   │   ├── facility/             # 倉庫施設関連テンプレート
│   │   ├── forklift/             # フォークリフト関連テンプレート
│   │   ├── includes/             # インクルードファイル
│   │   ├── inspection/           # 点検関連テンプレート
│   │   ├── operator/             # 操作者管理関連テンプレート
│   │   ├── pdf_management/       # PDF管理関連テンプレート
│   │   ├── repair/               # 修繕関連テンプレート
│   │   └── report/               # レポート関連テンプレート
│   └── utils/           # ユーティリティ関数
├── docs/                # ドキュメント
│   └── integration_test.md  # 統合テスト説明
├── migrations/          # データベースマイグレーション
├── tests/               # テストコード
│   ├── integration/     # 統合テスト
│   └── uploads/         # テスト用アップロードディレクトリ
├── app.py               # アプリケーションのエントリーポイント
├── build_windows_app.py # Windows用インストーラービルドスクリプト
├── config.py            # 設定ファイル
├── create_windows_shortcut.py # Windowsショートカット作成スクリプト
├── init_db.py           # データベース初期化スクリプト
├── add_sample_data.py   # サンプルデータ追加スクリプト
├── add_admin_user.py    # 管理者ユーザー作成スクリプト
├── fix_migration.py     # マイグレーション修正スクリプト
├── pdf_management.md    # PDF管理機能説明
├── pytest.ini           # pytestの設定ファイル
├── requirements.txt     # 依存パッケージリスト
├── run_integration_tests.py  # 統合テスト実行スクリプト
├── run_migration.py     # マイグレーション実行スクリプト
├── run_migration_windows.bat # Windows用マイグレーション実行バッチ
├── WINDOWS_INSTALLER_README.md # Windows用インストーラー作成手順
└── README.md            # このファイル
```

## 最新の更新内容

### 2025-05-23 更新
- レポート機能のエラーを修正：「Can only use .dt accessor with datetimelike values」エラーを解決
- 倉庫施設詳細画面のテンプレートエラーを修正：「Unexpected end of template. Jinja was looking for the following tags: 'endblock'」エラーを解決
- フォークリフト詳細画面の画像アップロード機能を修正：アップロードした画像がファイル一覧に表示されない問題を解決
- Windows用インストーラー作成機能を追加：EXEファイルと初回起動用のセットアップファイルを作成する機能を追加

### 2025-05-21 更新
- ログイン時のTypeErrorを修正：未認証状態で`current_user.is_admin()`が呼び出されるエラーを修正
- アプリケーションのデフォルトポートを54763から53319に変更

## 使用方法

1. 管理者ユーザーでログイン
2. ダッシュボード画面から全体の状況を確認
3. 「フォークリフト一覧」からフォークリフトの詳細情報を閲覧・編集
4. 「倉庫施設一覧」から倉庫施設の詳細情報を閲覧・編集
5. 「修繕履歴」から修繕記録を追加・編集
6. 「点検報告書」から各種点検表を作成・出力
   - バッテリー液量点検表
   - 定期自主検査記録表
   - 始業前点検報告書
7. 「年次点検」からフォークリフトの年次点検記録を管理
8. 「PDF管理」から点検報告書や修繕報告書のPDFを生成・アップロード・閲覧・ダウンロード
9. 「レポート」から各種レポートを生成・出力
10. 「CSVアップロード」からデータをインポート
11. 管理者は「ユーザー管理」からユーザーの追加・編集・削除が可能
12. 「操作者管理」から操作者情報を管理

## サンプルデータ

`add_sample_data.py`を実行すると、以下のサンプルデータが追加されます：

- フォークリフト：複数台（リーチ式/カウンター式、バッテリー/軽油の組み合わせ）
- 倉庫施設：複数箇所
- 修繕履歴：複数件（アワーメーター値付き）
- 点検記録：バッテリー液量点検、定期自主検査、始業前点検のサンプル
- 操作者：複数名

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