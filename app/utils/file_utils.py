import os
import re

def secure_filename_with_japanese(filename):
    """
    安全なファイル名を生成する関数（日本語対応版）
    通常のsecure_filenameは日本語を削除してしまうため、日本語を保持しつつ安全なファイル名を生成する
    """
    if not filename:
        return ""
    
    # ファイル名から拡張子を分離
    name, ext = os.path.splitext(filename)
    
    # 危険な文字を削除（パス区切り文字、制御文字など）
    # 日本語などの非ASCII文字は保持する
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    
    # 空白文字をアンダースコアに置換
    name = re.sub(r'\s+', '_', name)
    
    # ファイル名が空になった場合はデフォルト名を使用
    if not name:
        name = "file"
    
    # 拡張子を小文字に変換して結合
    return name + ext.lower()