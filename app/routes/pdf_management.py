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
    
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            file_path = os.path.join(pdf_dir, filename)
            file_stats = os.stat(file_path)
            pdf_files.append({
                'filename': filename,
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
        # ファイルが存在するか確認
        if 'pdf_file' not in request.files:
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        
        # ファイル名が空でないか確認
        if file.filename == '':
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        # ファイルが許可された拡張子を持つか確認
        if file and allowed_file(file.filename):
            # ファイル名を安全に保存
            filename = secure_filename(file.filename)
            
            # 重複を避けるためにUUIDを付加
            if '.' in filename:
                name, ext = filename.rsplit('.', 1)
                filename = f"{name}_{uuid.uuid4().hex}.{ext}"
            else:
                filename = f"{filename}_{uuid.uuid4().hex}.pdf"
            
            # ファイルを保存
            pdf_dir = ensure_pdf_directory()
            file_path = os.path.join(pdf_dir, filename)
            file.save(file_path)
            
            flash('PDFファイルがアップロードされました', 'success')
            return redirect(url_for('pdf_management.index'))
        else:
            flash('許可されていないファイル形式です。PDFファイルのみアップロード可能です。', 'danger')
            return redirect(request.url)
    
    return render_template('pdf_management/upload.html')

@pdf_management_bp.route('/view/<filename>')
def view_pdf(filename):
    pdf_dir = ensure_pdf_directory()
    file_path = os.path.join(pdf_dir, secure_filename(filename))
    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path, mimetype='application/pdf')

@pdf_management_bp.route('/download/<filename>')
def download_pdf(filename):
    pdf_dir = ensure_pdf_directory()
    file_path = os.path.join(pdf_dir, secure_filename(filename))
    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path, as_attachment=True, download_name=filename)

@pdf_management_bp.route('/delete/<filename>', methods=['POST'])
def delete_pdf(filename):
    pdf_dir = ensure_pdf_directory()
    file_path = os.path.join(pdf_dir, secure_filename(filename))
    
    if not os.path.exists(file_path):
        abort(404)
    
    try:
        os.remove(file_path)
        flash('PDFファイルが削除されました', 'success')
    except Exception as e:
        flash(f'ファイル削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('pdf_management.index'))

@pdf_management_bp.route('/generate/inspection/<int:inspection_id>/<inspection_type>')
def generate_inspection_pdf(inspection_id, inspection_type):
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
            return redirect(url_for('pdf_management.view_pdf', filename=filename))
            
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
            return redirect(url_for('pdf_management.view_pdf', filename=filename))
            
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
            return redirect(url_for('pdf_management.view_pdf', filename=filename))
        
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
            return redirect(url_for('pdf_management.view_pdf', filename=filename))
            
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
            return redirect(url_for('pdf_management.view_pdf', filename=filename))
            
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
            return redirect(url_for('pdf_management.view_pdf', filename=filename))
            
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
        
        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf') and search_term.lower() in filename.lower():
                file_path = os.path.join(pdf_dir, filename)
                file_stats = os.stat(file_path)
                pdf_files.append({
                    'filename': filename,
                    'size': file_stats.st_size,
                    'created_at': datetime.fromtimestamp(file_stats.st_ctime),
                    'modified_at': datetime.fromtimestamp(file_stats.st_mtime)
                })
        
        # 修正日時の降順でソート
        pdf_files.sort(key=lambda x: x['modified_at'], reverse=True)
        
        return render_template('pdf_management/search_results.html', pdf_files=pdf_files, search_term=search_term)
    
    return render_template('pdf_management/search.html')