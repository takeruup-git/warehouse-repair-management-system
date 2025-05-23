import os
import sys
import winshell
from win32com.client import Dispatch

def create_shortcut(target_path, shortcut_path, description, icon_path=None):
    """Windowsショートカットを作成する"""
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.Description = description
    if icon_path:
        shortcut.IconLocation = icon_path
    shortcut.save()
    print(f"ショートカットを作成しました: {shortcut_path}")

def create_application_shortcuts():
    """アプリケーションのショートカットを作成する"""
    # アプリケーションのパス
    app_path = os.path.abspath("dist/倉庫修繕費管理システム/倉庫修繕費管理システム.exe")
    first_run_path = os.path.abspath("dist/倉庫修繕費管理システム/初回起動.bat")
    
    # アイコンファイルのパス
    icon_path = os.path.abspath("app/static/img/favicon.ico")
    if not os.path.exists(icon_path):
        icon_path = app_path
    
    # デスクトップパスを取得
    desktop_path = winshell.desktop()
    
    # デスクトップショートカットを作成
    app_shortcut_path = os.path.join(desktop_path, "倉庫修繕費管理システム.lnk")
    create_shortcut(app_path, app_shortcut_path, "倉庫修繕費管理システム", icon_path)
    
    first_run_shortcut_path = os.path.join(desktop_path, "倉庫修繕費管理システム - 初回起動.lnk")
    create_shortcut(first_run_path, first_run_shortcut_path, "倉庫修繕費管理システム - 初回起動", icon_path)
    
    # スタートメニューショートカットを作成
    start_menu_path = winshell.start_menu()
    start_menu_folder = os.path.join(start_menu_path, "Programs", "倉庫修繕費管理システム")
    
    if not os.path.exists(start_menu_folder):
        os.makedirs(start_menu_folder)
    
    app_start_shortcut = os.path.join(start_menu_folder, "倉庫修繕費管理システム.lnk")
    create_shortcut(app_path, app_start_shortcut, "倉庫修繕費管理システム", icon_path)
    
    first_run_start_shortcut = os.path.join(start_menu_folder, "倉庫修繕費管理システム - 初回起動.lnk")
    create_shortcut(first_run_path, first_run_start_shortcut, "倉庫修繕費管理システム - 初回起動", icon_path)

if __name__ == "__main__":
    try:
        create_application_shortcuts()
        print("ショートカットの作成が完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)