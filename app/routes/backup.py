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
    current_app.logger.info("バックアップ作成を開始")
    
    try:
        # バックアップディレクトリの確認
        backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            current_app.logger.info(f"バックアップディレクトリを作成しました: {backup_dir}")
        
        # バックアップファイル名（タイムスタンプ付き）
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        current_app.logger.info(f"バックアップファイル名: {backup_filename}")
        
        # 一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            current_app.logger.info(f"一時ディレクトリを作成: {temp_dir}")
            
            # データベースのバックアップ
            # 開発環境と本番環境の両方に対応するため、複数のパスを試す
            possible_db_paths = [
                os.path.join(current_app.root_path, '..', 'instance', 'warehouse.db'),  # 標準パス
                os.path.join(current_app.root_path, '..', 'instance', 'dev-app.db'),    # 開発環境パス
                os.path.join(current_app.instance_path, 'warehouse.db'),                # Flaskのinstance_pathを使用
                os.path.join(current_app.instance_path, 'dev-app.db')                  # 開発環境のinstance_path
            ]
            
            # 実際に存在するデータベースファイルを探す
            db_path = None
            for path in possible_db_paths:
                norm_path = os.path.normpath(path)
                if os.path.exists(norm_path):
                    db_path = norm_path
                    current_app.logger.info(f"既存のデータベースファイルを見つけました: {db_path}")
                    break
            
            # データベースファイルが見つからない場合は、デフォルトパスを使用
            if not db_path:
                db_path = os.path.normpath(possible_db_paths[0])
                current_app.logger.warning(f"既存のデータベースファイルが見つからないため、デフォルトパスを使用します: {db_path}")
                if not os.path.exists(os.path.dirname(db_path)):
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    current_app.logger.info(f"データベースディレクトリを作成しました: {os.path.dirname(db_path)}")
            
            db_backup_path = os.path.join(temp_dir, 'warehouse.db')
            
            try:
                # データベースをコピー
                if os.path.exists(db_path):
                    # SQLiteのバックアップAPIを使用
                    conn = sqlite3.connect(db_path)
                    backup_conn = sqlite3.connect(db_backup_path)
                    conn.backup(backup_conn)
                    conn.close()
                    backup_conn.close()
                    current_app.logger.info(f"データベースをバックアップしました: {db_path} -> {db_backup_path}")
                else:
                    # データベースファイルが存在しない場合は空のファイルを作成
                    with open(db_backup_path, 'w') as f:
                        pass
                    current_app.logger.warning(f"データベースファイルが存在しないため、空のファイルを作成しました: {db_backup_path}")
            except Exception as e:
                current_app.logger.error(f"データベースバックアップ中にエラーが発生しました: {str(e)}")
                # エラーが発生しても続行する
            
            # アップロードファイルのバックアップ
            uploads_dir = current_app.config['UPLOAD_FOLDER']
            uploads_backup_dir = os.path.join(temp_dir, 'uploads')
            
            try:
                if os.path.exists(uploads_dir):
                    shutil.copytree(uploads_dir, uploads_backup_dir, ignore=shutil.ignore_patterns('backups'))
                    current_app.logger.info(f"アップロードファイルをバックアップしました: {uploads_dir} -> {uploads_backup_dir}")
                else:
                    # アップロードディレクトリが存在しない場合は作成
                    os.makedirs(uploads_backup_dir)
                    current_app.logger.warning(f"アップロードディレクトリが存在しないため、空のディレクトリを作成しました: {uploads_backup_dir}")
            except Exception as e:
                current_app.logger.error(f"アップロードファイルのバックアップ中にエラーが発生しました: {str(e)}")
                # エラーが発生しても続行する
            
            # バックアップ情報を作成
            backup_info = {
                'created_at': timestamp,
                'created_by': current_user.full_name or current_user.username,
                'version': current_app.config.get('VERSION', '1.0.0'),
                'database_path': db_path,
                'uploads_dir': uploads_dir
            }
            
            # バックアップ情報をJSONファイルに保存
            try:
                with open(os.path.join(temp_dir, 'backup_info.json'), 'w', encoding='utf-8') as f:
                    json.dump(backup_info, f, ensure_ascii=False, indent=2)
                current_app.logger.info(f"バックアップ情報を保存しました: {backup_info}")
            except Exception as e:
                current_app.logger.error(f"バックアップ情報の保存中にエラーが発生しました: {str(e)}")
                # エラーが発生しても続行する
            
            # ZIPファイルを作成
            try:
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # データベースを追加
                    if os.path.exists(db_backup_path):
                        zipf.write(db_backup_path, 'warehouse.db')
                        current_app.logger.info(f"データベースをZIPに追加しました: {db_backup_path}")
                    
                    # バックアップ情報を追加
                    if os.path.exists(os.path.join(temp_dir, 'backup_info.json')):
                        zipf.write(os.path.join(temp_dir, 'backup_info.json'), 'backup_info.json')
                        current_app.logger.info("バックアップ情報をZIPに追加しました")
                    
                    # アップロードファイルを追加
                    if os.path.exists(uploads_backup_dir):
                        file_count = 0
                        for root, dirs, files in os.walk(uploads_backup_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, temp_dir)
                                try:
                                    zipf.write(file_path, arcname)
                                    file_count += 1
                                except Exception as e:
                                    current_app.logger.error(f"ファイルのZIP追加中にエラーが発生しました: {file_path}, エラー: {str(e)}")
                        current_app.logger.info(f"アップロードファイルをZIPに追加しました: {file_count}個")
                
                current_app.logger.info(f"バックアップZIPファイルを作成しました: {backup_path}")
                flash('バックアップが正常に作成されました', 'success')
            except Exception as e:
                current_app.logger.error(f"ZIPファイルの作成中にエラーが発生しました: {str(e)}")
                raise
    except Exception as e:
        current_app.logger.error(f"バックアップの作成中にエラーが発生しました: {str(e)}")
        flash(f'バックアップの作成中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('backup.index'))

@backup_bp.route('/download/<filename>')
@login_required
def download_backup(filename):
    """バックアップファイルをダウンロード"""
    current_app.logger.info(f"バックアップファイルダウンロードを開始: {filename}")
    
    # ファイル名の安全性チェック
    if '..' in filename or filename.startswith('/'):
        current_app.logger.error(f"不正なファイル名が指定されました: {filename}")
        flash('不正なファイル名が指定されました', 'danger')
        return redirect(url_for('backup.index'))
    
    backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    # ファイルの存在確認
    if os.path.exists(file_path):
        # ファイルが通常のファイルであることを確認
        if not os.path.isfile(file_path):
            current_app.logger.error(f"指定されたパスはファイルではありません: {file_path}")
            flash('指定されたパスはファイルではありません', 'danger')
            return redirect(url_for('backup.index'))
        
        try:
            current_app.logger.info(f"バックアップファイルをダウンロードします: {file_path}")
            return send_file(file_path, as_attachment=True, download_name=filename)
        except Exception as e:
            current_app.logger.error(f"バックアップファイルのダウンロード中にエラーが発生しました: {str(e)}")
            flash(f'バックアップファイルのダウンロード中にエラーが発生しました: {str(e)}', 'danger')
            return redirect(url_for('backup.index'))
    else:
        current_app.logger.warning(f"指定されたバックアップファイルが見つかりません: {file_path}")
        flash('指定されたバックアップファイルが見つかりません', 'danger')
        return redirect(url_for('backup.index'))

@backup_bp.route('/restore/<filename>', methods=['POST'])
@login_required
def restore_backup(filename):
    """バックアップからシステムを復元"""
    # 最初にログ出力を設定
    current_app.logger.info(f"バックアップ復元を開始: {filename}")
    
    try:
        backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
        backup_path = os.path.join(backup_dir, filename)
        
        # バックアップファイルの存在確認
        if not os.path.exists(backup_path):
            current_app.logger.error(f"バックアップファイルが見つかりません: {backup_path}")
            flash('指定されたバックアップファイルが見つかりません', 'danger')
            return redirect(url_for('backup.index'))
        
        # 一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            current_app.logger.info(f"一時ディレクトリを作成: {temp_dir}")
            
            # ZIPファイルを展開
            try:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                current_app.logger.info(f"バックアップファイルを展開しました: {backup_path}")
            except Exception as e:
                current_app.logger.error(f"バックアップファイルの展開中にエラーが発生しました: {str(e)}")
                flash(f'バックアップファイルの展開中にエラーが発生しました: {str(e)}', 'danger')
                return redirect(url_for('backup.index'))
            
            # バックアップ情報を読み込み
            backup_info_path = os.path.join(temp_dir, 'backup_info.json')
            if os.path.exists(backup_info_path):
                try:
                    with open(backup_info_path, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                        # バックアップ情報を表示
                        flash(f'バックアップ情報: 作成日時 {backup_info.get("created_at")}, 作成者 {backup_info.get("created_by")}', 'info')
                        current_app.logger.info(f"バックアップ情報: {backup_info}")
                except Exception as e:
                    current_app.logger.warning(f"バックアップ情報の読み込み中にエラーが発生しました: {str(e)}")
            
            # データベースを復元
            db_backup_path = os.path.join(temp_dir, 'warehouse.db')
            
            # 現在のデータベースパスを取得
            # 開発環境と本番環境の両方に対応するため、複数のパスを試す
            possible_db_paths = [
                os.path.join(current_app.root_path, '..', 'instance', 'warehouse.db'),  # 標準パス
                os.path.join(current_app.root_path, '..', 'instance', 'dev-app.db'),    # 開発環境パス
                os.path.join(current_app.instance_path, 'warehouse.db'),                # Flaskのinstance_pathを使用
                os.path.join(current_app.instance_path, 'dev-app.db')                  # 開発環境のinstance_path
            ]
            
            # 実際に存在するデータベースファイルを探す
            db_path = None
            for path in possible_db_paths:
                norm_path = os.path.normpath(path)
                if os.path.exists(norm_path):
                    db_path = norm_path
                    current_app.logger.info(f"既存のデータベースファイルを見つけました: {db_path}")
                    break
            
            # データベースファイルが見つからない場合は、デフォルトパスを使用
            if not db_path:
                db_path = os.path.normpath(possible_db_paths[0])
                current_app.logger.warning(f"既存のデータベースファイルが見つからないため、デフォルトパスを使用します: {db_path}")
            
            # パスを正規化
            db_backup_path = os.path.normpath(db_backup_path)
            
            # 既存のデータベースをバックアップ
            db_before_restore = os.path.join(backup_dir, f"before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            db_before_restore = os.path.normpath(db_before_restore)
            
            # ソースとデスティネーションが同じでないことを確認
            if os.path.abspath(db_path) != os.path.abspath(db_before_restore):
                try:
                    shutil.copy2(db_path, db_before_restore)
                    current_app.logger.info(f"既存のデータベースをバックアップしました: {db_before_restore}")
                except Exception as e:
                    current_app.logger.error(f"データベースバックアップ中にエラーが発生しました: {str(e)}")
            else:
                current_app.logger.warning(f"データベースバックアップをスキップしました: ソースとデスティネーションが同じです")
            
            # データベースを復元
            # 既存のデータベースを閉じる
            from app.models import db
            try:
                db.session.close_all()
                db.engine.dispose()
                current_app.logger.info("データベース接続を閉じました")
            except Exception as e:
                current_app.logger.warning(f"データベース接続を閉じる際にエラーが発生しました: {str(e)}")
            
            try:
                # バックアップファイルの存在確認
                if not os.path.exists(db_backup_path):
                    current_app.logger.error(f"バックアップデータベースファイルが見つかりません: {db_backup_path}")
                    raise ValueError(f"バックアップデータベースファイルが見つかりません: {db_backup_path}")
                
                # ソースとデスティネーションが同じでないことを確認
                if os.path.abspath(db_backup_path) != os.path.abspath(db_path):
                    # 親ディレクトリが存在することを確認
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    
                    # データベースファイルをコピー
                    shutil.copy2(db_backup_path, db_path)
                    current_app.logger.info(f"データベースファイルをコピーしました: {db_backup_path} -> {db_path}")
                    
                    # 権限を設定
                    try:
                        os.chmod(db_path, 0o666)
                        current_app.logger.info(f"データベースファイルの権限を設定しました: {db_path}")
                    except Exception as e:
                        current_app.logger.warning(f"データベースファイルの権限設定中にエラーが発生しました: {str(e)}")
                    
                    # データベース接続を再確立
                    try:
                        # SQLAlchemyエンジンを再作成
                        db.engine.dispose()
                        db.create_all()
                        db.session.commit()
                        current_app.logger.info("データベース接続を再確立しました")
                    except Exception as e:
                        current_app.logger.error(f"データベース接続の再確立中にエラーが発生しました: {str(e)}")
                        # エラーが発生しても続行する
                    
                    # データベース復元の成功をログに記録
                    current_app.logger.info(f"データベースを正常に復元しました: {db_path}")
                else:
                    current_app.logger.error(f"データベース復元をスキップしました: ソースとデスティネーションが同じです")
                    raise ValueError(f"データベース復元エラー: ソースとデスティネーションが同じです - {db_backup_path}")
            except Exception as e:
                current_app.logger.error(f"データベース復元中にエラーが発生しました: {str(e)}")
                flash(f'データベース復元中にエラーが発生しました: {str(e)}', 'danger')
                return redirect(url_for('backup.index'))
            
            # アップロードファイルを復元
            uploads_dir = current_app.config['UPLOAD_FOLDER']
            uploads_backup_dir = os.path.join(temp_dir, 'uploads')
            
            # パスを正規化
            uploads_dir = os.path.normpath(uploads_dir)
            uploads_backup_dir = os.path.normpath(uploads_backup_dir)
            
            # 既存のアップロードディレクトリをバックアップ
            if os.path.exists(uploads_dir):
                uploads_before_restore = os.path.join(backup_dir, f"uploads_before_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                uploads_before_restore = os.path.normpath(uploads_before_restore)
                
                # ソースとデスティネーションが同じでないことを確認
                if os.path.abspath(uploads_dir) != os.path.abspath(uploads_before_restore):
                    try:
                        shutil.copytree(uploads_dir, uploads_before_restore, ignore=shutil.ignore_patterns('backups'))
                        current_app.logger.info(f"既存のアップロードディレクトリをバックアップしました: {uploads_before_restore}")
                    except Exception as e:
                        current_app.logger.error(f"アップロードディレクトリのバックアップ中にエラーが発生しました: {str(e)}")
                else:
                    current_app.logger.warning(f"アップロードディレクトリのバックアップをスキップしました: ソースとデスティネーションが同じです")
            
            # アップロードファイルを復元
            if os.path.exists(uploads_backup_dir):
                try:
                    # 現在のバックアップファイルを保存
                    current_backups = []
                    backups_dir = os.path.join(uploads_dir, 'backups')
                    if os.path.exists(backups_dir):
                        current_backups = [os.path.join(backups_dir, f) for f in os.listdir(backups_dir)]
                        current_app.logger.info(f"現在のバックアップファイルを保存: {len(current_backups)}個")
                    
                    # アップロードディレクトリを削除して復元（バックアップディレクトリを除く）
                    for item in os.listdir(uploads_dir):
                        if item != 'backups':  # バックアップディレクトリは保持
                            item_path = os.path.join(uploads_dir, item)
                            try:
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                else:
                                    os.remove(item_path)
                                current_app.logger.info(f"アップロードディレクトリのアイテムを削除: {item_path}")
                            except Exception as e:
                                current_app.logger.error(f"アップロードディレクトリのアイテム削除中にエラーが発生しました: {str(e)}")
                    
                    # バックアップからファイルを復元
                    for item in os.listdir(uploads_backup_dir):
                        src = os.path.join(uploads_backup_dir, item)
                        dst = os.path.join(uploads_dir, item)
                        
                        # パスを正規化
                        src = os.path.normpath(src)
                        dst = os.path.normpath(dst)
                        
                        if item == 'backups':  # バックアップディレクトリは特別処理
                            current_app.logger.info(f"バックアップディレクトリはスキップします: {src}")
                            continue
                        
                        # ソースとデスティネーションが同じでないことを確認
                        if os.path.abspath(src) == os.path.abspath(dst):
                            current_app.logger.warning(f"ファイル復元をスキップしました: ソースとデスティネーションが同じです - {src}")
                            continue
                            
                        try:
                            if os.path.isdir(src):
                                if os.path.exists(dst):
                                    shutil.rmtree(dst)
                                shutil.copytree(src, dst)
                            else:
                                if os.path.exists(dst):
                                    os.remove(dst)
                                shutil.copy2(src, dst)
                            current_app.logger.info(f"ファイルを復元しました: {src} -> {dst}")
                        except Exception as e:
                            current_app.logger.error(f"ファイル復元中にエラーが発生しました: {src} -> {dst}, エラー: {str(e)}")
                    
                    # バックアップディレクトリが存在しない場合は作成
                    if not os.path.exists(backups_dir):
                        os.makedirs(backups_dir)
                        current_app.logger.info(f"バックアップディレクトリを作成しました: {backups_dir}")
                    
                    # 現在のバックアップファイルを復元
                    for backup_file in current_backups:
                        if os.path.exists(backup_file):
                            dst = os.path.join(backups_dir, os.path.basename(backup_file))
                            
                            # パスを正規化
                            backup_file = os.path.normpath(backup_file)
                            dst = os.path.normpath(dst)
                            
                            # ソースとデスティネーションが同じでないことを確認
                            if os.path.abspath(backup_file) != os.path.abspath(dst):
                                try:
                                    shutil.copy2(backup_file, dst)
                                    current_app.logger.info(f"バックアップファイルを復元しました: {backup_file} -> {dst}")
                                except Exception as e:
                                    current_app.logger.error(f"バックアップファイルの復元中にエラーが発生しました: {backup_file} -> {dst}, エラー: {str(e)}")
                            else:
                                current_app.logger.warning(f"バックアップファイルの復元をスキップしました: ソースとデスティネーションが同じです - {backup_file}")
                    
                    # アップロードファイル復元の成功をログに記録
                    current_app.logger.info(f"アップロードファイルを正常に復元しました: {uploads_dir}")
                except Exception as e:
                    current_app.logger.error(f"アップロードファイル復元中にエラーが発生しました: {str(e)}")
                    flash(f'アップロードファイル復元中にエラーが発生しました: {str(e)}', 'danger')
                    return redirect(url_for('backup.index'))
        
        flash('システムが正常に復元されました。変更を完全に反映するには、アプリケーションを再起動してください。', 'success')
        current_app.logger.info("システムが正常に復元されました")
        
        # データベース接続を再確立して即時反映を試みる
        from app.models import db
        try:
            db.session.close_all()
            db.engine.dispose()
            db.create_all()
            db.session.commit()
            current_app.logger.info("データベース接続を再確立しました")
        except Exception as e:
            current_app.logger.error(f"データベース接続の再確立中にエラーが発生しました: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"復元中にエラーが発生しました: {str(e)}")
        flash(f'復元中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('backup.index'))

@backup_bp.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_backup(filename):
    """バックアップファイルを削除"""
    current_app.logger.info(f"バックアップファイル削除を開始: {filename}")
    
    backup_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    # ファイル名の安全性チェック
    if '..' in filename or filename.startswith('/'):
        current_app.logger.error(f"不正なファイル名が指定されました: {filename}")
        flash('不正なファイル名が指定されました', 'danger')
        return redirect(url_for('backup.index'))
    
    # ファイルの存在確認
    if os.path.exists(file_path):
        try:
            # ファイルが通常のファイルであることを確認
            if not os.path.isfile(file_path):
                current_app.logger.error(f"指定されたパスはファイルではありません: {file_path}")
                flash('指定されたパスはファイルではありません', 'danger')
                return redirect(url_for('backup.index'))
            
            # ファイルを削除
            os.remove(file_path)
            current_app.logger.info(f"バックアップファイルを削除しました: {file_path}")
            flash('バックアップファイルが削除されました', 'success')
        except PermissionError:
            current_app.logger.error(f"バックアップファイルの削除権限がありません: {file_path}")
            flash('バックアップファイルの削除権限がありません', 'danger')
        except Exception as e:
            current_app.logger.error(f"バックアップファイルの削除中にエラーが発生しました: {str(e)}")
            flash(f'バックアップファイルの削除中にエラーが発生しました: {str(e)}', 'danger')
    else:
        current_app.logger.warning(f"指定されたバックアップファイルが見つかりません: {file_path}")
        flash('指定されたバックアップファイルが見つかりません', 'danger')
    
    return redirect(url_for('backup.index'))