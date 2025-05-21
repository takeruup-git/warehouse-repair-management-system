from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from app.models import db, AuditLog
from app.models.forklift import Forklift
from app.models.inspection import BatteryFluidCheck, PeriodicSelfInspection, PreShiftInspection
from app.models.master import Employee
from datetime import datetime, timedelta
import os
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from config import Config

inspection_bp = Blueprint('inspection', __name__)

# 日本語フォントの登録
try:
    pdfmetrics.registerFont(TTFont('MSGothic', 'msgothic.ttc'))
except:
    # フォントが見つからない場合はデフォルトフォントを使用
    pass

@inspection_bp.route('/')
def index():
    return render_template('inspection/index.html')

@inspection_bp.route('/battery_fluid')
def battery_fluid():
    # バッテリー液量点検表一覧 - PDFをUploadして閲覧・管理する機能のみに変更
    from app.models.file import FileMetadata
    
    pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf', 'battery_fluid')
    pdf_files = []
    
    # ディレクトリが存在するか確認
    if os.path.exists(pdf_dir):
        # PDFファイルを取得
        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_dir, filename)
                file_stat = os.stat(file_path)
                
                # ファイルの相対パスを計算（UPLOADフォルダからの相対パス）
                relative_path = os.path.join('pdf', 'battery_fluid', filename)
                
                # メタデータからオリジナルのファイル名を取得
                metadata = FileMetadata.query.filter_by(file_path=relative_path).first()
                display_name = metadata.original_filename if metadata else filename
                
                # ファイル情報を取得
                pdf_files.append({
                    'name': display_name,  # オリジナルのファイル名を表示
                    'system_name': filename,  # システム内部のファイル名
                    'path': os.path.join('static', 'uploads', 'pdf', 'battery_fluid', filename),
                    'size': file_stat.st_size,
                    'created_at': datetime.fromtimestamp(file_stat.st_ctime)
                })
    else:
        # ディレクトリが存在しない場合は作成
        os.makedirs(pdf_dir, exist_ok=True)
    
    # 作成日時でソート
    pdf_files.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('inspection/battery_fluid/index.html', pdf_files=pdf_files)

@inspection_bp.route('/battery_fluid/create', methods=['GET', 'POST'])
def create_battery_fluid():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            check_date = datetime.strptime(request.form['check_date'], '%Y-%m-%d').date()
            forklift_id = int(request.form['forklift_id'])
            management_number = request.form['management_number']
            warehouse = request.form['warehouse']
            elapsed_years = float(request.form['elapsed_years'])
            fluid_level = request.form['fluid_level']
            
            refill_date = None
            if request.form.get('refill_date'):
                refill_date = datetime.strptime(request.form['refill_date'], '%Y-%m-%d').date()
                
            refiller = request.form.get('refiller', '')
            confirmation_date = datetime.strptime(request.form['confirmation_date'], '%Y-%m-%d').date()
            inspector = request.form['inspector']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # バッテリー液量点検表を作成
            check = BatteryFluidCheck(
                check_date=check_date,
                forklift_id=forklift_id,
                management_number=management_number,
                warehouse=warehouse,
                elapsed_years=elapsed_years,
                fluid_level=fluid_level,
                refill_date=refill_date,
                refiller=refiller,
                confirmation_date=confirmation_date,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(check)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='battery_fluid_check',
                operator=operator,
                details=f'バッテリー液量点検表 {management_number} を作成'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('バッテリー液量点検表が正常に作成されました。', 'success')
            return redirect(url_for('inspection.battery_fluid'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得（バッテリー式のみ）
    forklifts = Forklift.query.filter_by(power_source='battery').all()
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/battery_fluid/create.html',
                          forklifts=forklifts,
                          employees=employees)

@inspection_bp.route('/battery_fluid/<int:id>')
def view_battery_fluid(id):
    check = BatteryFluidCheck.query.get_or_404(id)
    return render_template('inspection/battery_fluid/view.html', check=check)

@inspection_bp.route('/battery_fluid/<int:id>/edit', methods=['GET', 'POST'])
def edit_battery_fluid(id):
    check = BatteryFluidCheck.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # フォームからデータを取得して更新
            check.check_date = datetime.strptime(request.form['check_date'], '%Y-%m-%d').date()
            check.fluid_level = request.form['fluid_level']
            
            if request.form.get('refill_date'):
                check.refill_date = datetime.strptime(request.form['refill_date'], '%Y-%m-%d').date()
            else:
                check.refill_date = None
                
            check.refiller = request.form.get('refiller', '')
            check.confirmation_date = datetime.strptime(request.form['confirmation_date'], '%Y-%m-%d').date()
            check.inspector = request.form['inspector']
            check.notes = request.form.get('notes', '')
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='battery_fluid_check',
                entity_id=id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'バッテリー液量点検表 ID:{id} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('バッテリー液量点検表が正常に更新されました。', 'success')
            return redirect(url_for('inspection.view_battery_fluid', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/battery_fluid/edit.html',
                          check=check,
                          employees=employees)

@inspection_bp.route('/battery_fluid/<int:id>/delete', methods=['POST'])
def delete_battery_fluid(id):
    check = BatteryFluidCheck.query.get_or_404(id)
    
    try:
        db.session.delete(check)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='battery_fluid_check',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'バッテリー液量点検表 ID:{id} を削除'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('バッテリー液量点検表が正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('inspection.battery_fluid'))

# バッテリー液量点検表エクスポート機能は削除されました

@inspection_bp.route('/periodic_self')
def periodic_self():
    # 定期自主検査記録表一覧 - PDFをUploadして閲覧・管理する機能のみに変更
    from app.models.file import FileMetadata
    
    pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf', 'periodic_self')
    pdf_files = []
    
    # ディレクトリが存在するか確認
    if os.path.exists(pdf_dir):
        # PDFファイルを取得
        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_dir, filename)
                file_stat = os.stat(file_path)
                
                # ファイルの相対パスを計算（UPLOADフォルダからの相対パス）
                relative_path = os.path.join('pdf', 'periodic_self', filename)
                
                # メタデータからオリジナルのファイル名を取得
                metadata = FileMetadata.query.filter_by(file_path=relative_path).first()
                display_name = metadata.original_filename if metadata else filename
                
                # ファイル情報を取得
                pdf_files.append({
                    'name': display_name,  # オリジナルのファイル名を表示
                    'system_name': filename,  # システム内部のファイル名
                    'path': os.path.join('static', 'uploads', 'pdf', 'periodic_self', filename),
                    'size': file_stat.st_size,
                    'created_at': datetime.fromtimestamp(file_stat.st_ctime)
                })
    else:
        # ディレクトリが存在しない場合は作成
        os.makedirs(pdf_dir, exist_ok=True)
    
    # 作成日時でソート
    pdf_files.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('inspection/periodic_self/index.html', pdf_files=pdf_files)

# 定期自主検査記録表エクスポート機能は削除されました

@inspection_bp.route('/periodic_self/<int:id>')
def view_periodic_self(id):
    inspection = PeriodicSelfInspection.query.get_or_404(id)
    return render_template('inspection/periodic_self/view.html', inspection=inspection)

@inspection_bp.route('/periodic_self/create', methods=['GET', 'POST'])
def create_periodic_self():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            management_number = request.form['management_number']
            hour_meter = request.form['hour_meter']
            travel_system_ok = 'travel_system_ok' in request.form
            loading_device_ok = 'loading_device_ok' in request.form
            electrical_system_ok = 'electrical_system_ok' in request.form
            brake_system_ok = 'brake_system_ok' in request.form
            steering_system_ok = 'steering_system_ok' in request.form
            inspector = request.form['inspector']
            notes = request.form['notes']
            operator = request.form['operator']
            
            # 定期自主検査記録表を作成
            inspection = PeriodicSelfInspection(
                inspection_date=inspection_date,
                management_number=management_number,
                hour_meter=hour_meter,
                travel_system_ok=travel_system_ok,
                loading_device_ok=loading_device_ok,
                electrical_system_ok=electrical_system_ok,
                brake_system_ok=brake_system_ok,
                steering_system_ok=steering_system_ok,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            db.session.commit()
            
            # 監査ログに記録
            log = AuditLog(
                action='create',
                entity_type='periodic_self_inspection',
                entity_id=inspection.id,
                operator=operator,
                details=f'定期自主検査記録表を作成しました。管理番号: {management_number}'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('定期自主検査記録表が作成されました', 'success')
            return redirect(url_for('inspection.periodic_self'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'作成中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    return render_template('inspection/periodic_self/create.html',
                          forklifts=forklifts,
                          inspection_results=Config.INSPECTION_RESULT_NAMES)

@inspection_bp.route('/periodic_self/<int:id>/delete', methods=['POST'])
def delete_periodic_self(id):
    inspection = PeriodicSelfInspection.query.get_or_404(id)
    
    try:
        db.session.delete(inspection)
        db.session.commit()
        
        # 監査ログに記録
        log = AuditLog(
            action='delete',
            entity_type='periodic_self_inspection',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'定期自主検査記録表を削除しました。管理番号: {inspection.management_number}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('定期自主検査記録表が削除されました', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('inspection.periodic_self'))
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            forklift_id = int(request.form['forklift_id'])
            management_number = request.form['management_number']
            inspection_type = request.form['inspection_type']
            motor_condition = request.form['motor_condition']
            tire_condition = request.form['tire_condition']
            fork_condition = request.form['fork_condition']
            repair_action = request.form['repair_action']
            inspector = request.form['inspector']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # 定期自主検査記録表を作成
            inspection = PeriodicSelfInspection(
                inspection_date=inspection_date,
                forklift_id=forklift_id,
                management_number=management_number,
                inspection_type=inspection_type,
                motor_condition=motor_condition,
                tire_condition=tire_condition,
                fork_condition=fork_condition,
                repair_action=repair_action,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='periodic_self_inspection',
                operator=operator,
                details=f'定期自主検査記録表 {management_number} を作成'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('定期自主検査記録表が正常に作成されました。', 'success')
            return redirect(url_for('inspection.periodic_self'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.filter_by(asset_status='active').all()
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/periodic_self/create.html',
                          forklifts=forklifts,
                          employees=employees,
                          inspection_results=Config.INSPECTION_RESULT_NAMES,
                          repair_actions=Config.REPAIR_ACTION_NAMES)

@inspection_bp.route('/pre_shift')
def pre_shift():
    # 始業前点検報告書一覧 - PDFをUploadして閲覧・管理する機能のみに変更
    from app.models.file import FileMetadata
    
    pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf', 'pre_shift')
    pdf_files = []
    
    # ディレクトリが存在するか確認
    if os.path.exists(pdf_dir):
        # PDFファイルを取得
        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_dir, filename)
                file_stat = os.stat(file_path)
                
                # ファイルの相対パスを計算（UPLOADフォルダからの相対パス）
                relative_path = os.path.join('pdf', 'pre_shift', filename)
                
                # メタデータからオリジナルのファイル名を取得
                metadata = FileMetadata.query.filter_by(file_path=relative_path).first()
                display_name = metadata.original_filename if metadata else filename
                
                # ファイル情報を取得
                pdf_files.append({
                    'name': display_name,  # オリジナルのファイル名を表示
                    'system_name': filename,  # システム内部のファイル名
                    'path': os.path.join('static', 'uploads', 'pdf', 'pre_shift', filename),
                    'size': file_stat.st_size,
                    'created_at': datetime.fromtimestamp(file_stat.st_ctime)
                })
    else:
        # ディレクトリが存在しない場合は作成
        os.makedirs(pdf_dir, exist_ok=True)
    
    # 作成日時でソート
    pdf_files.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('inspection/pre_shift/index.html', pdf_files=pdf_files)

@inspection_bp.route('/pre_shift/<int:id>')
def view_pre_shift(id):
    inspection = PreShiftInspection.query.get_or_404(id)
    return render_template('inspection/pre_shift/view.html', inspection=inspection)

@inspection_bp.route('/pre_shift/create', methods=['GET', 'POST'])
def create_pre_shift():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            management_number = request.form['management_number']
            tire_ok = 'tire_ok' in request.form
            brake_ok = 'brake_ok' in request.form
            battery_ok = 'battery_ok' in request.form
            oil_ok = 'oil_ok' in request.form
            fork_ok = 'fork_ok' in request.form
            chain_ok = 'chain_ok' in request.form
            mast_ok = 'mast_ok' in request.form
            warning_light_ok = 'warning_light_ok' in request.form
            horn_ok = 'horn_ok' in request.form
            inspector = request.form['inspector']
            notes = request.form['notes']
            operator = request.form['operator']
            
            # 始業前点検報告書を作成
            inspection = PreShiftInspection(
                inspection_date=inspection_date,
                management_number=management_number,
                tire_ok=tire_ok,
                brake_ok=brake_ok,
                battery_ok=battery_ok,
                oil_ok=oil_ok,
                fork_ok=fork_ok,
                chain_ok=chain_ok,
                mast_ok=mast_ok,
                warning_light_ok=warning_light_ok,
                horn_ok=horn_ok,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            db.session.commit()
            
            # 監査ログに記録
            log = AuditLog(
                action='create',
                entity_type='pre_shift_inspection',
                entity_id=inspection.id,
                operator=operator,
                details=f'始業前点検報告書を作成しました。管理番号: {management_number}'
            )
            db.session.add(log)
            db.session.commit()
            
            flash('始業前点検報告書が作成されました', 'success')
            return redirect(url_for('inspection.pre_shift'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'作成中にエラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    
    # 従業員一覧を取得
    employees = Employee.query.all() if 'Employee' in globals() else []
    
    return render_template('inspection/pre_shift/create.html',
                          forklifts=forklifts,
                          employees=employees,
                          inspection_results=Config.INSPECTION_RESULT_NAMES)

@inspection_bp.route('/pre_shift/<int:id>/delete', methods=['POST'])
def delete_pre_shift(id):
    inspection = PreShiftInspection.query.get_or_404(id)
    
    try:
        db.session.delete(inspection)
        db.session.commit()
        
        # 監査ログに記録
        log = AuditLog(
            action='delete',
            entity_type='pre_shift_inspection',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'始業前点検報告書を削除しました。管理番号: {inspection.management_number}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('始業前点検報告書が削除されました', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('inspection.pre_shift'))
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            inspection_date = datetime.strptime(request.form['inspection_date'], '%Y-%m-%d').date()
            forklift_id = int(request.form['forklift_id'])
            management_number = request.form['management_number']
            inspection_type = request.form['inspection_type']
            hour_meter = int(request.form['hour_meter'])
            operating_hours = float(request.form['operating_hours'])
            fluid_refill = request.form.get('fluid_refill')
            if fluid_refill:
                fluid_refill = float(fluid_refill)
            
            engine_oil = None
            brake_condition = None
            battery_fluid = None
            tire_pressure = None
            
            if inspection_type == 'engine':
                engine_oil = request.form['engine_oil']
                brake_condition = request.form['brake_condition']
            else:  # battery
                battery_fluid = request.form['battery_fluid']
                tire_pressure = request.form['tire_pressure']
            
            inspector = request.form['inspector']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # 始業前点検報告書を作成
            inspection = PreShiftInspection(
                inspection_date=inspection_date,
                forklift_id=forklift_id,
                management_number=management_number,
                inspection_type=inspection_type,
                hour_meter=hour_meter,
                operating_hours=operating_hours,
                fluid_refill=fluid_refill,
                engine_oil=engine_oil,
                brake_condition=brake_condition,
                battery_fluid=battery_fluid,
                tire_pressure=tire_pressure,
                inspector=inspector,
                notes=notes,
                operator=operator
            )
            
            db.session.add(inspection)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='pre_shift_inspection',
                operator=operator,
                details=f'始業前点検報告書 {management_number} を作成'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('始業前点検報告書が正常に作成されました。', 'success')
            return redirect(url_for('inspection.pre_shift'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # フォークリフト一覧を取得
    forklifts = Forklift.query.filter_by(asset_status='active').all()
    
    # 従業員一覧を取得
    employees = Employee.query.filter_by(is_active=True).all()
    
    return render_template('inspection/pre_shift/create.html',
                          forklifts=forklifts,
                          employees=employees)