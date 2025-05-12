from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file, abort
from app.models import db
from app.models.forklift import Forklift, ForkliftRepair
from app.models.facility import Facility, FacilityRepair
from app.models.inspection import BatteryFluidCheck, PeriodicSelfInspection, PreShiftInspection
from app.models.other_repair import OtherRepair
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from config import Config

pdf_management_bp = Blueprint('pdf_management', __name__)

# 日本語フォントの登録
try:
    pdfmetrics.registerFont(TTFont('MSGothic', 'msgothic.ttc'))
except:
    # フォントが見つからない場合はデフォルトフォントを使用
    pass

# PDFファイルの保存ディレクトリを確認・作成
def ensure_pdf_directory():
    pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf')
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
    return pdf_dir

# 許可されるファイル拡張子
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pdf_management_bp.route('/')
def index():
    # PDFファイルの一覧を取得
    pdf_dir = ensure_pdf_directory()
    pdf_files = []
    
    # メインディレクトリとサブディレクトリの両方を検索
    for root, dirs, files in os.walk(pdf_dir):
        for filename in files:
            if filename.endswith('.pdf'):
                file_path = os.path.join(root, filename)
                file_stats = os.stat(file_path)
                
                # ファイルパスからrelative_pathを作成
                relative_path = os.path.relpath(file_path, os.path.join(current_app.root_path, 'static', 'uploads'))
                display_path = os.path.join('static', 'uploads', relative_path)
                
                pdf_files.append({
                    'filename': filename,
                    'path': display_path,
                    'size': file_stats.st_size,
                    'created_at': datetime.fromtimestamp(file_stats.st_ctime),
                    'modified_at': datetime.fromtimestamp(file_stats.st_mtime)
                })
    
    # 修正日時の降順でソート
    pdf_files.sort(key=lambda x: x['modified_at'], reverse=True)
    
    return render_template('pdf_management/index.html', pdf_files=pdf_files)

@pdf_management_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # PDFファイルのアップロード
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            
            # ファイル名が空でないか確認
            if file.filename == '':
                flash('ファイルが選択されていません', 'danger')
                return redirect(request.url)
            
            # ファイルが許可された拡張子を持つか確認
            if file and allowed_file(file.filename):
                # オリジナルのファイル名を保持（日本語対応）
                original_filename = file.filename
                # 日本語ファイル名の場合はUUIDを使用
                if any(ord(c) > 127 for c in original_filename):
                    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'pdf'
                    filename = f"{uuid.uuid4().hex}.{ext}"
                else:
                    filename = secure_filename(original_filename)
                
                # 重複を避けるためにタイムスタンプ付きのサブディレクトリを作成
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # アセットタイプとIDが指定されている場合はそれを含める
                asset_type = request.form.get('asset_type', '')
                asset_id = request.form.get('asset_id', '')
                description = request.form.get('description', '')
                
                if asset_type and asset_id:
                    unique_dir = os.path.join('pdf', asset_type, str(asset_id), date_str)
                else:
                    unique_dir = os.path.join('pdf', date_str)
                
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # ファイルを保存
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # 監査ログを記録
                operator = request.form.get('operator_name', 'システム')
                log_details = f'PDFファイル {filename} をアップロード'
                if description:
                    log_details += f' (説明: {description})'
                
                audit_log = AuditLog(
                    action='upload',
                    entity_type='pdf',
                    entity_id=asset_id if asset_id else None,
                    operator=operator,
                    details=log_details
                )
                db.session.add(audit_log)
                db.session.commit()
                
                flash('PDFファイルがアップロードされました', 'success')
                
                # リダイレクト先を決定
                if asset_type == 'forklift' and asset_id:
                    return redirect(url_for('forklift.view', id=asset_id))
                elif asset_type == 'facility' and asset_id:
                    return redirect(url_for('facility.view', id=asset_id))
                else:
                    return redirect(url_for('pdf_management.index'))
            else:
                flash('許可されていないファイル形式です。PDFファイルのみアップロード可能です。', 'danger')
                return redirect(request.url)
        
        # 画像ファイルのアップロード
        elif 'image_file' in request.files:
            file = request.files['image_file']
            
            # ファイル名が空でないか確認
            if file.filename == '':
                flash('ファイルが選択されていません', 'danger')
                return redirect(request.url)
            
            # 画像ファイルの拡張子を確認
            allowed_image_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_image_extensions:
                # オリジナルのファイル名を保持（日本語対応）
                original_filename = file.filename
                # 日本語ファイル名の場合はUUIDを使用
                if any(ord(c) > 127 for c in original_filename):
                    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
                    filename = f"{uuid.uuid4().hex}.{ext}"
                else:
                    filename = secure_filename(original_filename)
                
                # 重複を避けるためにタイムスタンプ付きのサブディレクトリを作成
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # アセットタイプとIDが指定されている場合はそれを含める
                asset_type = request.form.get('asset_type', '')
                asset_id = request.form.get('asset_id', '')
                description = request.form.get('description', '')
                
                if asset_type and asset_id:
                    unique_dir = os.path.join('images', asset_type, str(asset_id), date_str)
                else:
                    unique_dir = os.path.join('images', date_str)
                
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # ファイルを保存
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # 監査ログを記録
                operator = request.form.get('operator_name', 'システム')
                log_details = f'画像ファイル {filename} をアップロード'
                if description:
                    log_details += f' (説明: {description})'
                
                audit_log = AuditLog(
                    action='upload',
                    entity_type='image',
                    entity_id=asset_id if asset_id else None,
                    operator=operator,
                    details=log_details
                )
                db.session.add(audit_log)
                db.session.commit()
                
                flash('画像ファイルがアップロードされました', 'success')
                
                # リダイレクト先を決定
                if asset_type == 'forklift' and asset_id:
                    return redirect(url_for('forklift.view', id=asset_id))
                elif asset_type == 'facility' and asset_id:
                    return redirect(url_for('facility.view', id=asset_id))
                else:
                    return redirect(url_for('pdf_management.index'))
            else:
                flash('許可されていない画像形式です。PNG, JPG, JPEG, GIF形式のみアップロード可能です。', 'danger')
                return redirect(request.url)
        else:
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
    
    return render_template('pdf_management/upload.html')

@pdf_management_bp.route('/view/<path:filepath>')
def view_pdf(filepath):
    # ファイルパスを安全に処理
    safe_path = os.path.normpath(filepath)
    if safe_path.startswith('..') or safe_path.startswith('/'):
        abort(404)
    
    file_path = os.path.join(current_app.root_path, safe_path)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    return send_file(file_path, mimetype='application/pdf')

@pdf_management_bp.route('/view_by_name/<filename>')
def view_pdf_by_name(filename):
    # PDFディレクトリからファイルを取得
    pdf_dir = ensure_pdf_directory()
    file_path = os.path.join(pdf_dir, filename)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    return send_file(file_path, mimetype='application/pdf')

@pdf_management_bp.route('/download/<path:filepath>')
def download_pdf(filepath):
    # ファイルパスを安全に処理
    safe_path = os.path.normpath(filepath)
    if safe_path.startswith('..') or safe_path.startswith('/'):
        abort(404)
    
    file_path = os.path.join(current_app.root_path, safe_path)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    # オリジナルのファイル名を取得
    filename = os.path.basename(file_path)
    
    return send_file(file_path, as_attachment=True, download_name=filename)

@pdf_management_bp.route('/delete/<path:filepath>', methods=['POST'])
def delete_pdf(filepath):
    # ファイルパスを安全に処理
    safe_path = os.path.normpath(filepath)
    if safe_path.startswith('..') or safe_path.startswith('/'):
        abort(404)
    
    file_path = os.path.join(current_app.root_path, safe_path)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    try:
        os.remove(file_path)
        
        # 空のディレクトリを削除
        dir_path = os.path.dirname(file_path)
        if os.path.exists(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
            
        flash('PDFファイルが削除されました', 'success')
    except Exception as e:
        flash(f'ファイル削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('pdf_management.index'))

@pdf_management_bp.route('/generate/inspection/<int:inspection_id>/<inspection_type>')
@pdf_management_bp.route('/generate/inspection/<int:inspection_id>/<inspection_type>/<show_empty>')
def generate_inspection_pdf(inspection_id, inspection_type, show_empty=None):
    try:
        if inspection_type == 'battery_fluid':
            inspection = BatteryFluidCheck.query.get_or_404(inspection_id)
            forklift = Forklift.query.get_or_404(inspection.forklift_id)
            
            # PDFファイルを生成
            filename = f"battery_fluid_check_{forklift.management_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_dir = ensure_pdf_directory()
            file_path = os.path.join(pdf_dir, filename)
            
            # PDFを生成
            c = canvas.Canvas(file_path, pagesize=A4)
            
            # 日本語フォントを設定
            try:
                c.setFont('MSGothic', 10)
            except:
                c.setFont('Helvetica', 10)
            
            # タイトル
            c.setFont('MSGothic', 16)
            c.drawString(30 * mm, 280 * mm, 'バッテリー液量点検表')
            
            # 基本情報
            c.setFont('MSGothic', 10)
            c.drawString(30 * mm, 270 * mm, f'管理番号: {forklift.management_number}')
            c.drawString(30 * mm, 265 * mm, f'点検日: {inspection.check_date.strftime("%Y-%m-%d")}')
            c.drawString(30 * mm, 260 * mm, f'点検者: {inspection.inspector}')
            
            # 点検結果
            c.drawString(30 * mm, 250 * mm, '点検結果:')
            c.drawString(30 * mm, 245 * mm, f'液量: {"良" if inspection.fluid_level_ok else "不良"}')
            c.drawString(30 * mm, 240 * mm, f'比重: {"良" if inspection.specific_gravity_ok else "不良"}')
            
            # 備考
            c.drawString(30 * mm, 230 * mm, '備考:')
            
            # 備考テキストを複数行に分割して描画
            if inspection.notes:
                notes_lines = inspection.notes.split('\n')
                y = 225 * mm
                for line in notes_lines:
                    c.drawString(30 * mm, y, line)
                    y -= 5 * mm
            
            c.save()
            
            flash('点検報告書PDFが生成されました', 'success')
            return redirect(url_for('pdf_management.view_pdf_by_name', filename=filename))
            
        elif inspection_type == 'periodic_self':
            inspection = PeriodicSelfInspection.query.get_or_404(inspection_id)
            forklift = Forklift.query.get_or_404(inspection.forklift_id)
            
            # PDFファイルを生成
            filename = f"periodic_self_inspection_{forklift.management_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_dir = ensure_pdf_directory()
            file_path = os.path.join(pdf_dir, filename)
            
            # PDFを生成
            c = canvas.Canvas(file_path, pagesize=A4)
            
            # 日本語フォントを設定
            try:
                c.setFont('MSGothic', 10)
            except:
                c.setFont('Helvetica', 10)
            
            # タイトル
            c.setFont('MSGothic', 16)
            c.drawString(30 * mm, 280 * mm, '定期自主検査記録表')
            
            # 基本情報
            c.setFont('MSGothic', 10)
            c.drawString(30 * mm, 270 * mm, f'管理番号: {forklift.management_number}')
            c.drawString(30 * mm, 265 * mm, f'点検日: {inspection.inspection_date.strftime("%Y-%m-%d")}')
            c.drawString(30 * mm, 260 * mm, f'点検者: {inspection.inspector}')
            c.drawString(30 * mm, 255 * mm, f'アワーメーター: {inspection.hour_meter}')
            
            # 点検結果
            c.drawString(30 * mm, 245 * mm, '点検結果:')
            c.drawString(30 * mm, 240 * mm, f'走行装置: {"良" if inspection.travel_system_ok else "不良"}')
            c.drawString(30 * mm, 235 * mm, f'荷役装置: {"良" if inspection.loading_device_ok else "不良"}')
            c.drawString(30 * mm, 230 * mm, f'電気装置: {"良" if inspection.electrical_system_ok else "不良"}')
            c.drawString(30 * mm, 225 * mm, f'制動装置: {"良" if inspection.brake_system_ok else "不良"}')
            c.drawString(30 * mm, 220 * mm, f'操縦装置: {"良" if inspection.steering_system_ok else "不良"}')
            
            # 備考
            c.drawString(30 * mm, 210 * mm, '備考:')
            
            # 備考テキストを複数行に分割して描画
            if inspection.notes:
                notes_lines = inspection.notes.split('\n')
                y = 205 * mm
                for line in notes_lines:
                    c.drawString(30 * mm, y, line)
                    y -= 5 * mm
            
            c.save()
            
            flash('点検報告書PDFが生成されました', 'success')
            return redirect(url_for('pdf_management.view_pdf_by_name', filename=filename))
            
        elif inspection_type == 'pre_shift':
            inspection = PreShiftInspection.query.get_or_404(inspection_id)
            forklift = Forklift.query.get_or_404(inspection.forklift_id)
            
            # PDFファイルを生成
            filename = f"pre_shift_inspection_{forklift.management_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_dir = ensure_pdf_directory()
            file_path = os.path.join(pdf_dir, filename)
            
            # PDFを生成
            c = canvas.Canvas(file_path, pagesize=A4)
            
            # 日本語フォントを設定
            try:
                c.setFont('MSGothic', 10)
            except:
                c.setFont('Helvetica', 10)
            
            # タイトル
            c.setFont('MSGothic', 16)
            c.drawString(30 * mm, 280 * mm, '始業前点検報告書')
            
            # 基本情報
            c.setFont('MSGothic', 10)
            c.drawString(30 * mm, 270 * mm, f'管理番号: {forklift.management_number}')
            c.drawString(30 * mm, 265 * mm, f'点検日: {inspection.inspection_date.strftime("%Y-%m-%d")}')
            c.drawString(30 * mm, 260 * mm, f'点検者: {inspection.inspector}')
            
            # 点検結果
            c.drawString(30 * mm, 250 * mm, '点検結果:')
            c.drawString(30 * mm, 245 * mm, f'タイヤ: {"良" if inspection.tire_ok else "不良"}')
            c.drawString(30 * mm, 240 * mm, f'ブレーキ: {"良" if inspection.brake_ok else "不良"}')
            c.drawString(30 * mm, 235 * mm, f'バッテリー: {"良" if inspection.battery_ok else "不良"}')
            c.drawString(30 * mm, 230 * mm, f'オイル: {"良" if inspection.oil_ok else "不良"}')
            c.drawString(30 * mm, 225 * mm, f'フォーク: {"良" if inspection.fork_ok else "不良"}')
            c.drawString(30 * mm, 220 * mm, f'チェーン: {"良" if inspection.chain_ok else "不良"}')
            c.drawString(30 * mm, 215 * mm, f'マスト: {"良" if inspection.mast_ok else "不良"}')
            c.drawString(30 * mm, 210 * mm, f'警告灯: {"良" if inspection.warning_light_ok else "不良"}')
            c.drawString(30 * mm, 205 * mm, f'ホーン: {"良" if inspection.horn_ok else "不良"}')
            
            # 備考
            c.drawString(30 * mm, 195 * mm, '備考:')
            
            # 備考テキストを複数行に分割して描画
            if inspection.notes:
                notes_lines = inspection.notes.split('\n')
                y = 190 * mm
                for line in notes_lines:
                    c.drawString(30 * mm, y, line)
                    y -= 5 * mm
            
            c.save()
            
            flash('点検報告書PDFが生成されました', 'success')
            return redirect(url_for('pdf_management.view_pdf_by_name', filename=filename))
        
        else:
            flash('無効な点検タイプです', 'danger')
            return redirect(url_for('pdf_management.index'))
            
    except Exception as e:
        flash(f'PDF生成中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('pdf_management.index'))

@pdf_management_bp.route('/generate/repair/<asset_type>/<int:repair_id>')
def generate_repair_pdf(asset_type, repair_id):
    try:
        if asset_type == 'forklift':
            repair = ForkliftRepair.query.get_or_404(repair_id)
            forklift = Forklift.query.get_or_404(repair.forklift_id)
            
            # PDFファイルを生成
            filename = f"forklift_repair_{forklift.management_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_dir = ensure_pdf_directory()
            file_path = os.path.join(pdf_dir, filename)
            
            # PDFを生成
            c = canvas.Canvas(file_path, pagesize=A4)
            
            # 日本語フォントを設定
            try:
                c.setFont('MSGothic', 10)
            except:
                c.setFont('Helvetica', 10)
            
            # タイトル
            c.setFont('MSGothic', 16)
            c.drawString(30 * mm, 280 * mm, 'フォークリフト修繕報告書')
            
            # 基本情報
            c.setFont('MSGothic', 10)
            c.drawString(30 * mm, 270 * mm, f'管理番号: {forklift.management_number}')
            c.drawString(30 * mm, 265 * mm, f'修繕日: {repair.repair_date.strftime("%Y-%m-%d")}')
            c.drawString(30 * mm, 260 * mm, f'アワーメーター: {repair.hour_meter}')
            c.drawString(30 * mm, 255 * mm, f'修繕費用: {repair.repair_cost:,}円')
            c.drawString(30 * mm, 250 * mm, f'修繕理由: {Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason)}')
            
            # 修繕項目
            c.drawString(30 * mm, 240 * mm, '修繕項目:')
            c.drawString(30 * mm, 235 * mm, repair.repair_item)
            
            # 備考
            c.drawString(30 * mm, 225 * mm, '備考:')
            
            # 備考テキストを複数行に分割して描画
            if repair.notes:
                notes_lines = repair.notes.split('\n')
                y = 220 * mm
                for line in notes_lines:
                    c.drawString(30 * mm, y, line)
                    y -= 5 * mm
            
            c.save()
            
            flash('修繕報告書PDFが生成されました', 'success')
            return redirect(url_for('pdf_management.view_pdf_by_name', filename=filename))
            
        elif asset_type == 'facility':
            repair = FacilityRepair.query.get_or_404(repair_id)
            facility = Facility.query.get_or_404(repair.facility_id)
            
            # PDFファイルを生成
            filename = f"facility_repair_{facility.warehouse_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_dir = ensure_pdf_directory()
            file_path = os.path.join(pdf_dir, filename)
            
            # PDFを生成
            c = canvas.Canvas(file_path, pagesize=A4)
            
            # 日本語フォントを設定
            try:
                c.setFont('MSGothic', 10)
            except:
                c.setFont('Helvetica', 10)
            
            # タイトル
            c.setFont('MSGothic', 16)
            c.drawString(30 * mm, 280 * mm, '倉庫施設修繕報告書')
            
            # 基本情報
            c.setFont('MSGothic', 10)
            c.drawString(30 * mm, 270 * mm, f'倉庫番号: {facility.warehouse_number}')
            c.drawString(30 * mm, 265 * mm, f'修繕日: {repair.repair_date.strftime("%Y-%m-%d")}')
            c.drawString(30 * mm, 260 * mm, f'階層: {repair.floor}')
            c.drawString(30 * mm, 255 * mm, f'修繕費用: {repair.repair_cost:,}円')
            c.drawString(30 * mm, 250 * mm, f'修繕理由: {Config.REPAIR_REASON_NAMES.get(repair.repair_reason, repair.repair_reason)}')
            
            # 修繕項目
            c.drawString(30 * mm, 240 * mm, '修繕項目:')
            c.drawString(30 * mm, 235 * mm, repair.repair_item)
            
            # 備考
            c.drawString(30 * mm, 225 * mm, '備考:')
            
            # 備考テキストを複数行に分割して描画
            if repair.notes:
                notes_lines = repair.notes.split('\n')
                y = 220 * mm
                for line in notes_lines:
                    c.drawString(30 * mm, y, line)
                    y -= 5 * mm
            
            c.save()
            
            flash('修繕報告書PDFが生成されました', 'success')
            return redirect(url_for('pdf_management.view_pdf_by_name', filename=filename))
            
        elif asset_type == 'other':
            repair = OtherRepair.query.get_or_404(repair_id)
            
            # PDFファイルを生成
            filename = f"other_repair_{repair.target_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_dir = ensure_pdf_directory()
            file_path = os.path.join(pdf_dir, filename)
            
            # PDFを生成
            c = canvas.Canvas(file_path, pagesize=A4)
            
            # 日本語フォントを設定
            try:
                c.setFont('MSGothic', 10)
            except:
                c.setFont('Helvetica', 10)
            
            # タイトル
            c.setFont('MSGothic', 16)
            c.drawString(30 * mm, 280 * mm, 'その他修繕報告書')
            
            # 基本情報
            c.setFont('MSGothic', 10)
            c.drawString(30 * mm, 270 * mm, f'対象名: {repair.target_name}')
            c.drawString(30 * mm, 265 * mm, f'修繕日: {repair.repair_date.strftime("%Y-%m-%d")}')
            c.drawString(30 * mm, 260 * mm, f'カテゴリ: {repair.category}')
            c.drawString(30 * mm, 255 * mm, f'修繕費用: {repair.repair_cost:,}円')
            c.drawString(30 * mm, 250 * mm, f'業者: {repair.contractor}')
            
            # 備考
            c.drawString(30 * mm, 240 * mm, '備考:')
            
            # 備考テキストを複数行に分割して描画
            if repair.notes:
                notes_lines = repair.notes.split('\n')
                y = 235 * mm
                for line in notes_lines:
                    c.drawString(30 * mm, y, line)
                    y -= 5 * mm
            
            c.save()
            
            flash('修繕報告書PDFが生成されました', 'success')
            return redirect(url_for('pdf_management.view_pdf_by_name', filename=filename))
            
        else:
            flash('無効な資産タイプです', 'danger')
            return redirect(url_for('pdf_management.index'))
            
    except Exception as e:
        flash(f'PDF生成中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('pdf_management.index'))

@pdf_management_bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        
        pdf_dir = ensure_pdf_directory()
        pdf_files = []
        
        # メインディレクトリとサブディレクトリの両方を検索
        for root, dirs, files in os.walk(pdf_dir):
            for filename in files:
                if filename.endswith('.pdf') and search_term.lower() in filename.lower():
                    file_path = os.path.join(root, filename)
                    file_stats = os.stat(file_path)
                    
                    # ファイルパスからrelative_pathを作成
                    relative_path = os.path.relpath(file_path, os.path.join(current_app.root_path, 'static', 'uploads'))
                    display_path = os.path.join('static', 'uploads', relative_path)
                    
                    pdf_files.append({
                        'filename': filename,
                        'path': display_path,
                        'size': file_stats.st_size,
                        'created_at': datetime.fromtimestamp(file_stats.st_ctime),
                        'modified_at': datetime.fromtimestamp(file_stats.st_mtime)
                    })
        
        # 修正日時の降順でソート
        pdf_files.sort(key=lambda x: x['modified_at'], reverse=True)
        
        return render_template('pdf_management/search_results.html', pdf_files=pdf_files, search_term=search_term)
    
    return render_template('pdf_management/search.html')

@pdf_management_bp.route('/upload/inspection/<inspection_type>', methods=['GET', 'POST'])
def upload_inspection_pdf(inspection_type):
    if request.method == 'POST':
        # ファイルが存在するか確認
        if 'pdf_file' not in request.files:
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        
        # ファイル名が空でないか確認
        if file.filename == '':
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        # ファイル形式が正しいか確認
        if file and allowed_file(file.filename):
            # ファイル名を安全に保存
            filename = secure_filename(file.filename)
            
            # 点検タイプに応じたディレクトリを確認・作成
            pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf', inspection_type)
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            
            # ファイルを保存
            file_path = os.path.join(pdf_dir, filename)
            file.save(file_path)
            
            flash('PDFファイルがアップロードされました', 'success')
            
            # 点検タイプに応じたリダイレクト先を設定
            if inspection_type == 'battery_fluid':
                return redirect(url_for('inspection.battery_fluid'))
            elif inspection_type == 'periodic_self':
                return redirect(url_for('inspection.periodic_self'))
            elif inspection_type == 'pre_shift':
                return redirect(url_for('inspection.pre_shift'))
            else:
                return redirect(url_for('pdf_management.index'))
        else:
            flash('許可されていないファイル形式です。PDFファイルを選択してください。', 'danger')
            return redirect(request.url)
    
    # 点検タイプに応じたタイトルを設定
    title = ''
    if inspection_type == 'battery_fluid':
        title = 'バッテリー液量点検表'
    elif inspection_type == 'periodic_self':
        title = '定期自主検査記録表'
    elif inspection_type == 'pre_shift':
        title = '始業前点検報告書'
    
    return render_template('pdf_management/upload_inspection.html', inspection_type=inspection_type, title=title)