# 定期自主検査記録表フォーマット出力

## 概要
フォークリフトマスタを基にExcelフォーマット出力機能を実装します。

## 機能
- 全稼働中フォークリフトのフォーマットを1ファイルで生成
- シートごとに管理番号、機種、動力、検査項目を出力

## 実装計画
1. Excelテンプレート作成
2. openpyxlによるデータ埋め込み処理実装
3. フォークリフト一覧画面にフォーマット出力ボタン追加