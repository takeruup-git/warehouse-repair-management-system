# 倉庫修繕管理システム テスト

このディレクトリには倉庫修繕管理システムのテストコードが含まれています。

## テスト構成

- `conftest.py`: テスト設定とフィクスチャ
- `integration/`: 統合テスト
- `uploads/`: テスト用アップロードディレクトリ

## 統合テスト

統合テストは以下の機能を検証します：

1. CSVアップロード機能
2. PDF管理機能
3. 操作者管理機能
4. ダッシュボード改良
5. 年次点検機能
6. フォーマット出力機能

## テスト実行方法

### すべての統合テストを実行

```bash
python run_integration_tests.py
```

### 特定のテストのみ実行

```bash
# 特定のテストファイルを実行
pytest -xvs tests/integration/test_csv_upload.py

# 特定のテスト関数を実行
pytest -xvs tests/integration/test_csv_upload.py::test_csv_upload_functionality
```

### カバレッジレポートの生成

```bash
pytest --cov=app --cov-report=html tests/
```

これにより `htmlcov` ディレクトリにHTMLカバレッジレポートが生成されます。

## テスト環境

テストは以下の環境で実行されます：

- データベース: SQLite（メモリ内）
- アップロードディレクトリ: `tests/uploads/`
- CSRF保護: 無効（テスト用）

## テストユーザー

テスト用のデフォルトユーザー：

- ユーザー名: `testuser`
- パスワード: `password`