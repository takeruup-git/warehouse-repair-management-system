# Issue #3: PDF管理システムの実装

## 概要

PDF管理システムは、倉庫修繕費管理システム内でPDFファイルを一元管理するための機能です。点検報告書や修繕報告書のPDFを生成、アップロード、閲覧、ダウンロード、検索、削除することができます。

## 主な機能

1. **PDF一覧表示**
   - システム内のすべてのPDFファイルを一覧表示
   - ファイル名、サイズ、作成日時、更新日時を表示
   - 表示、ダウンロード、削除の操作が可能

2. **PDFアップロード**
   - 外部で作成したPDFファイルをシステムにアップロード
   - ファイル名の重複を避けるためにUUIDを付加
   - PDFファイルのみアップロード可能（拡張子チェック）

3. **PDF生成**
   - 点検報告書（バッテリー液量点検表、定期自主検査記録表、始業前点検報告書）のPDF生成
   - 修繕報告書（フォークリフト、倉庫施設、その他）のPDF生成
   - 生成したPDFはシステム内に保存され、一覧から管理可能

4. **PDF検索**
   - ファイル名によるPDFファイルの検索
   - 検索結果からの表示、ダウンロード、削除が可能

5. **PDF表示・ダウンロード**
   - ブラウザ内でのPDFファイルの表示
   - PDFファイルのダウンロード

6. **PDF削除**
   - 不要になったPDFファイルの削除
   - 削除前の確認ダイアログ表示

## 技術的実装

- **ルーティング**: `/pdf/*` のURLパスで各機能にアクセス
- **ストレージ**: PDFファイルは `app/static/uploads/pdf` ディレクトリに保存
- **PDF生成**: ReportLabライブラリを使用してPDFを動的に生成
- **セキュリティ**: ファイル名のサニタイズ、拡張子チェックによるセキュリティ対策
- **UI**: Bootstrap 5を使用した直感的なユーザーインターフェース

## 使用方法

1. ナビゲーションメニューから「PDF管理」を選択
2. 「PDF一覧」でシステム内のPDFファイルを確認
3. 「PDFアップロード」で外部PDFファイルをアップロード
4. 「PDF検索」でファイル名によるPDF検索
5. 各資産の詳細ページから点検報告書や修繕報告書のPDFを生成

## 今後の拡張予定

- PDFのプレビュー機能の強化
- PDFファイルのタグ付け機能
- OCRによるPDF内のテキスト検索機能
- PDFファイルの一括ダウンロード機能
