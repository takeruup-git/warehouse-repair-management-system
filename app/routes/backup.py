from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
import os
import shutil
import sqlite3
import datetime
import zipfile
import tempfile
import json

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/')
@login_required
def index():
    """バックアップ管理画面を表示"""
    # バックアップディレクトリの確認
    backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 既存のバックアップファイルを取得
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip'):
            file_path = os.path.join(backup_dir, filename)
            file_stats = os.stat(file_path)
            backups.append({
                'name': filename,
                'size': file_stats.st_size,
                'created_at': datetime.datetime.fromtimestamp(file_stats.st_ctime)
            })
    
    # 作成日時の降順でソート
    backups.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('backup/index.html', backups=backups)

@backup_bp.route('/create', methods=['POST'])
@login_required
def create_backup():
    """システムのバックアップを作成"""
    try:
        # バックアップディレクトリの確認
        backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # バックアップファイル名（タイムスタンプ付き）
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            # データベースのバックアップ
            db_path = os.path.join(current_app.root_path, '..', 'instance', 'warehouse.db')
            db_backup_path = os.path.join(temp_dir, 'warehouse.db')
            
            # データベースをコピー
            conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(db_backup_path)
            conn.backup(backup_conn)
            conn.close()
            backup_conn.close()
            
            # アップロードファイルのバックアップ
            uploads_dir = current_app.config['UPLOAD_FOLDER']
            uploads_backup_dir = os.path.join(temp_dir, 'uploads')
            if os.path.exists(uploads_dir):
                shutil.copytree(uploads_dir, uploads_backup_dir, ignore=shutil.ignore_patterns('backups'))
            
            # バックアップ情報を作成
            backup_info = {
                'created_at': timestamp,
                'created_by': current_user.username,
                'version': current_app.config.get('VERSION', '1.0.0')
            }
            
            # バックアップ情報をJSONファイルに保存
            with open(os.path.join(temp_dir, 'backup_info.json'), 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # ZIPファイルを作成
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # データベースを追加
                zipf.write(db_backup_path, 'warehouse.db')
                
                # バックアップ情報を追加
                zipf.write(os.path.join(temp_dir, 'backup_info.json'), 'backup_info.json')
                
                # アップロードファイルを追加
                if os.path.exists(uploads_backup_dir):
                    for root, dirs, files in os.walk(uploads_backup_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
        
        flash('バックアップが正常に作成されました', 'success')
    except Exception as e:
        flash(f'バックアップの作成中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('backup.index'))

@backup_bp.route('/download/<filename>')
@login_required
def download_backup(filename):
    """バックアップファイルをダウンロード"""
    backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('指定されたバックアップファイルが見つかりません', 'danger')
        return redirect(url_for('backup.index'))

@backup_bp.route('/restore/<filename>', methods=['POST'])
@login_required
def restore_backup(filename):
    """バックアップからシステムを復元"""
    try:
        backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
        backup_path = os.path.join(backup_dir, filename)
        
        if not os.path.exists(backup_path):
            flash('指定されたバックアップファイルが見つかりません', 'danger')
            return redirect(url_for('backup.index'))
        
        # 一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            # ZIPファイルを展開
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # バックアップ情報を読み込み
            backup_info_path = os.path.join(temp_dir, 'backup_info.json')
            if os.path.exists(backup_info_path):
                with open(backup_info_path, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                    # バックアップ情報を表示
                    flash(f'バックアップ情報: 作成日時 {backup_info.get("created_at")}, 作成者 {backup_info.get("created_by")}', 'info')
            
            # データベースを復元
            db_backup_path = os.path.join(temp_dir, 'warehouse.db')
            db_path = os.path.join(current_app.root_path, '..', 'instance', 'warehouse.db')
            
            # 既存のデータベースをバックアップ
            db_before_restore = os.path.join(backup_dir, f"before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy2(db_path, db_before_restore)
            
            # データベースを復元
            # 既存のデータベースを閉じる
            from app.models import db
            db.session.close_all()
            db.engine.dispose()
            
            try:
                # データベースファイルをコピー
                shutil.copy2(db_backup_path, db_path)
                
                # 権限を設定
                os.chmod(db_path, 0o666)
                
                # データベース復元の成功をログに記録
                current_app.logger.info(f"データベースを正常に復元しました: {db_path}")
            except Exception as e:
                current_app.logger.error(f"データベース復元中にエラーが発生しました: {str(e)}")
                raise
            
            # アップロードファイルを復元
            uploads_dir = current_app.config['UPLOAD_FOLDER']
            uploads_backup_dir = os.path.join(temp_dir, 'uploads')
            
            # 既存のアップロードディレクトリをバックアップ
            if os.path.exists(uploads_dir):
                uploads_before_restore = os.path.join(backup_dir, f"uploads_before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copytree(uploads_dir, uploads_before_restore, ignore=shutil.ignore_patterns('backups'))
            
            # アップロードファイルを復元
            if os.path.exists(uploads_backup_dir):
                try:
                    # 現在のバックアップファイルを保存
                    current_backups = []
                    backups_dir = os.path.join(uploads_dir, 'backups')
                    if os.path.exists(backups_dir):
                        current_backups = [os.path.join(backups_dir, f) for f in os.listdir(backups_dir)]
                    
                    # アップロードディレクトリを削除して復元（バックアップディレクトリを除く）
                    for item in os.listdir(uploads_dir):
                        if item != 'backups':  # バックアップディレクトリは保持
                            item_path = os.path.join(uploads_dir, item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                    
                    # バックアップからファイルを復元
                    for item in os.listdir(uploads_backup_dir):
                        src = os.path.join(uploads_backup_dir, item)
                        dst = os.path.join(uploads_dir, item)
                        
                        if item == 'backups':  # バックアップディレクトリは特別処理
                            continue
                            
                        if os.path.isdir(src):
                            if os.path.exists(dst):
                                shutil.rmtree(dst)
                            shutil.copytree(src, dst)
                        else:
                            if os.path.exists(dst):
                                os.remove(dst)
                            shutil.copy2(src, dst)
                    
                    # バックアップディレクトリが存在しない場合は作成
                    if not os.path.exists(backups_dir):
                        os.makedirs(backups_dir)
                    
                    # 現在のバックアップファイルを復元
                    for backup_file in current_backups:
                        if os.path.exists(backup_file):
                            dst = os.path.join(backups_dir, os.path.basename(backup_file))
                            shutil.copy2(backup_file, dst)
                    
                    # アップロードファイル復元の成功をログに記録
                    current_app.logger.info(f"アップロードファイルを正常に復元しました: {uploads_dir}")
                except Exception as e:
                    current_app.logger.error(f"アップロードファイル復元中にエラーが発生しました: {str(e)}")
                    raise
        
        flash('システムが正常に復元されました。アプリケーションを再起動してください。', 'success')
    except Exception as e:
        flash(f'復元中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('backup.index'))

@backup_bp.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_backup(filename):
    """バックアップファイルを削除"""
    backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            flash('バックアップファイルが削除されました', 'success')
        except Exception as e:
            flash(f'バックアップファイルの削除中にエラーが発生しました: {str(e)}', 'danger')
    else:
        flash('指定されたバックアップファイルが見つかりません', 'danger')
    
    return redirect(url_for('backup.index'))