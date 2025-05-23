import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_exe():
    print("Windows用の実行ファイルをビルドしています...")
    
    # ビルドディレクトリをクリーンアップ
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # PyInstallerコマンドを構築
    pyinstaller_cmd = [
        'pyinstaller',
        '--name=倉庫修繕費管理システム',
        # '--icon=app/static/img/favicon.ico',  # アイコンファイルが存在しないためコメントアウト
        '--add-data=app/templates;app/templates',
        '--add-data=app/static;app/static',
        '--add-data=migrations;migrations',
        '--hidden-import=sqlalchemy.sql.default_comparator',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=flask_migrate',
        '--hidden-import=flask_wtf',
        '--hidden-import=wtforms',
        '--hidden-import=jinja2',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=matplotlib',
        '--hidden-import=reportlab',
        '--hidden-import=openpyxl',
        '--hidden-import=xlsxwriter',
        '--hidden-import=PIL',
        '--hidden-import=dateutil',
        '--hidden-import=email_validator',
        '--hidden-import=flask_login',
        '--hidden-import=flask_session',
        '--onedir',
        'app.py'
    ]
    
    # PyInstallerを実行
    result = subprocess.run(pyinstaller_cmd)
    
    if result.returncode != 0:
        print("PyInstallerの実行中にエラーが発生しました。")
        return False
    
    # ビルド結果を確認
    dist_dir = 'dist/倉庫修繕費管理システム'
    if not os.path.exists(dist_dir):
        print("ビルドディレクトリが作成されませんでした。")
        return False
    
    print("実行ファイルのビルドが完了しました。")
    
    # 初回起動用のバッチファイルを作成
    create_first_run_batch()
    
    # 通常起動用のバッチファイルを作成
    create_run_batch()
    
    # Inno Setupスクリプトを作成
    create_inno_setup_script()
    
    print("セットアップファイルの準備が完了しました。")
    return True

def create_first_run_batch():
    """初回起動用のバッチファイルを作成"""
    dist_dir = 'dist/倉庫修繕費管理システム'
    
    # ディレクトリが存在しない場合は作成
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
        print(f"ディレクトリを作成しました: {dist_dir}")
    
    batch_content = """@echo off
echo 倉庫修繕費管理システム - 初回起動
echo データベースを初期化しています...

cd %~dp0
set FLASK_APP=app.py
set FLASK_ENV=production

REM データベースの初期化
"倉庫修繕費管理システム.exe" init_db.py

REM 管理者ユーザーの作成
"倉庫修繕費管理システム.exe" add_admin_user.py

REM サンプルデータの追加（オプション）
echo サンプルデータを追加しますか？ (Y/N)
set /p CHOICE=選択: 
if /i "%CHOICE%"=="Y" (
    "倉庫修繕費管理システム.exe" add_sample_data.py
)

REM アプリケーションの起動
start "" "倉庫修繕費管理システム.exe"

echo 初期セットアップが完了しました。
echo 次回からは「倉庫修繕費管理システム.exe」を直接実行してください。
pause
"""
    
    try:
        with open(f'{dist_dir}/初回起動.bat', 'w', encoding='shift-jis') as f:
            f.write(batch_content)
        print("初回起動用バッチファイルを作成しました。")
    except Exception as e:
        print(f"初回起動用バッチファイルの作成中にエラーが発生しました: {e}")

def create_run_batch():
    """通常起動用のバッチファイルを作成"""
    dist_dir = 'dist/倉庫修繕費管理システム'
    
    # ディレクトリが存在しない場合は作成
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
        print(f"ディレクトリを作成しました: {dist_dir}")
    
    batch_content = """@echo off
echo 倉庫修繕費管理システム - 起動中...
cd %~dp0
start "" "倉庫修繕費管理システム.exe"
"""
    
    try:
        with open(f'{dist_dir}/起動.bat', 'w', encoding='shift-jis') as f:
            f.write(batch_content)
        print("通常起動用バッチファイルを作成しました。")
    except Exception as e:
        print(f"通常起動用バッチファイルの作成中にエラーが発生しました: {e}")

def create_inno_setup_script():
    """Inno Setupスクリプトを作成"""
    iss_content = """
#define MyAppName "倉庫修繕費管理システム"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://www.example.com/"
#define MyAppExeName "倉庫修繕費管理システム.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-4A5B-9C8D-7E6F5A4B3C2D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer
OutputBaseFilename=倉庫修繕費管理システム_セットアップ
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\\倉庫修繕費管理システム\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\初回起動"; Filename: "{app}\\初回起動.bat"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\初回起動.bat"; Description: "初回セットアップを実行"; Flags: nowait postinstall skipifsilent
"""
    
    # ライセンスファイルがない場合は作成
    if not os.path.exists('LICENSE.txt'):
        with open('LICENSE.txt', 'w') as f:
            f.write("倉庫修繕費管理システム ライセンス\n\n")
            f.write("Copyright (c) 2025 Your Company\n\n")
            f.write("このソフトウェアは、使用許諾契約に基づいて提供されています。\n")
            f.write("無断での複製・配布は禁止されています。\n")
    
    # インストーラー出力ディレクトリを作成
    os.makedirs('installer', exist_ok=True)
    
    with open('倉庫修繕費管理システム.iss', 'w', encoding='utf-8') as f:
        f.write(iss_content)
    
    print("Inno Setupスクリプトを作成しました。")

if __name__ == "__main__":
    success = build_exe()
    if success:
        print("ビルドプロセスが完了しました。")
        print("Inno Setupを使用してインストーラーを作成するには、以下のコマンドを実行してください：")
        print("iscc 倉庫修繕費管理システム.iss")
    else:
        print("ビルドプロセス中にエラーが発生しました。")
        sys.exit(1)