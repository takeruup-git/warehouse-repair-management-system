from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app.models import db, AuditLog
from app.models.forklift import ForkliftRepair
from app.models.facility import FacilityRepair
from app.models.other_repair import OtherRepair
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config

repair_bp = Blueprint('repair', __name__)

@repair_bp.route('/')
def index():
    # 修繕履歴一覧を取得
    forklift_repairs = ForkliftRepair.query.order_by(ForkliftRepair.repair_date.desc()).all()
    facility_repairs = FacilityRepair.query.order_by(FacilityRepair.repair_date.desc()).all()
    other_repairs = OtherRepair.query.order_by(OtherRepair.repair_date.desc()).all()
    
    return render_template('repair/index.html',
                          forklift_repairs=forklift_repairs,
                          facility_repairs=facility_repairs,
                          other_repairs=other_repairs,
                          repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES,
                          repair_reasons=Config.REPAIR_REASON_NAMES)

@repair_bp.route('/forklift/<int:id>')
def view_forklift_repair(id):
    repair = ForkliftRepair.query.get_or_404(id)
    return render_template('repair/view_forklift.html', repair=repair, repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES, repair_reasons=Config.REPAIR_REASON_NAMES)

@repair_bp.route('/facility/<int:id>')
def view_facility_repair(id):
    repair = FacilityRepair.query.get_or_404(id)
    return render_template('repair/view_facility.html', repair=repair, repair_reasons=Config.REPAIR_REASON_NAMES)

@repair_bp.route('/other/<int:id>')
def view_other_repair(id):
    repair = OtherRepair.query.get_or_404(id)
    return render_template('repair/view_other.html', repair=repair)

@repair_bp.route('/forklift/<int:id>/edit', methods=['GET', 'POST'])
def edit_forklift_repair(id):
    repair = ForkliftRepair.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # バージョンチェック（楽観的ロック）
            form_version = int(request.form['version'])
            if form_version != repair.version:
                flash('この修繕履歴は他のユーザーによって更新されました。最新の情報を確認してください。', 'danger')
                return redirect(url_for('repair.edit_forklift_repair', id=id))
            
            # フォームからデータを取得して更新
            repair.repair_date = datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date()
            repair.contractor = request.form['contractor']
            repair.repair_target_type = request.form['repair_target_type']
            repair.repair_item = request.form['repair_item']
            repair.repair_cost = int(request.form['repair_cost'])
            repair.repair_reason = request.form['repair_reason']
            
            hour_meter = request.form.get('hour_meter')
            if hour_meter:
                repair.hour_meter = int(hour_meter)
            else:
                repair.hour_meter = None
                
            repair.notes = request.form.get('notes', '')
            
            # ファイルアップロード処理
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_photo_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                repair.photo_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_quotation_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                repair.quotation_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_approval_{approval_document.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                repair.approval_document_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            if 'completion_report' in request.files and request.files['completion_report'].filename:
                completion_report = request.files['completion_report']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_completion_{completion_report.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                completion_report_path = os.path.join(upload_dir, filename)
                completion_report.save(completion_report_path)
                repair.completion_report_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            # バージョンを更新
            repair.increment_version()
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='forklift_repair',
                entity_id=id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'フォークリフト修繕履歴 ID:{id} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('修繕履歴が正常に更新されました。', 'success')
            return redirect(url_for('repair.view_forklift_repair', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/edit_forklift.html',
                          repair=repair,
                          repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES,
                          repair_reasons=Config.REPAIR_REASON_NAMES)

@repair_bp.route('/facility/<int:id>/edit', methods=['GET', 'POST'])
def edit_facility_repair(id):
    repair = FacilityRepair.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # バージョンチェック（楽観的ロック）
            form_version = int(request.form['version'])
            if form_version != repair.version:
                flash('この修繕履歴は他のユーザーによって更新されました。最新の情報を確認してください。', 'danger')
                return redirect(url_for('repair.edit_facility_repair', id=id))
            
            # フォームからデータを取得して更新
            repair.repair_date = datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date()
            repair.floor = request.form['floor']
            repair.contractor = request.form['contractor']
            repair.repair_item = request.form['repair_item']
            repair.repair_cost = int(request.form['repair_cost'])
            repair.repair_reason = request.form['repair_reason']
            repair.notes = request.form.get('notes', '')
            
            # ファイルアップロード処理
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_photo_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                repair.photo_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_quotation_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                repair.quotation_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_approval_{approval_document.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                repair.approval_document_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            if 'completion_report' in request.files and request.files['completion_report'].filename:
                completion_report = request.files['completion_report']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_completion_{completion_report.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                completion_report_path = os.path.join(upload_dir, filename)
                completion_report.save(completion_report_path)
                repair.completion_report_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            # バージョンを更新
            repair.increment_version()
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='facility_repair',
                entity_id=id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'倉庫施設修繕履歴 ID:{id} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('修繕履歴が正常に更新されました。', 'success')
            return redirect(url_for('repair.view_facility_repair', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/edit_facility.html',
                          repair=repair,
                          repair_reasons=Config.REPAIR_REASON_NAMES)

@repair_bp.route('/other/create', methods=['GET', 'POST'])
def create_other_repair():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            repair_date = datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date()
            target_name = request.form['target_name']
            category = request.form['category']
            repair_cost = int(request.form['repair_cost'])
            contractor = request.form['contractor']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # ファイルアップロード処理
            photo_path = None
            quotation_path = None
            
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_photo_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'other')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                photo_path = f"/static/uploads/other/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_quotation_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'other')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                quotation_path = f"/static/uploads/other/{filename}"
            
            # その他修繕履歴を作成
            repair = OtherRepair(
                repair_date=repair_date,
                target_name=target_name,
                category=category,
                repair_cost=repair_cost,
                contractor=contractor,
                notes=notes,
                photo_path=photo_path,
                quotation_path=quotation_path,
                operator=operator
            )
            
            db.session.add(repair)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='other_repair',
                operator=operator,
                details=f'その他修繕履歴 {target_name} を追加'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('修繕履歴が正常に追加されました。', 'success')
            return redirect(url_for('repair.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/create_other.html')

@repair_bp.route('/other/<int:id>/edit', methods=['GET', 'POST'])
def edit_other_repair(id):
    repair = OtherRepair.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # バージョンチェック（楽観的ロック）
            form_version = int(request.form['version'])
            if form_version != repair.version:
                flash('この修繕履歴は他のユーザーによって更新されました。最新の情報を確認してください。', 'danger')
                return redirect(url_for('repair.edit_other_repair', id=id))
            
            # フォームからデータを取得して更新
            repair.repair_date = datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date()
            repair.target_name = request.form['target_name']
            repair.category = request.form['category']
            repair.repair_cost = int(request.form['repair_cost'])
            repair.contractor = request.form['contractor']
            repair.notes = request.form.get('notes', '')
            
            # ファイルアップロード処理
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_photo_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'other')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                repair.photo_path = f"/static/uploads/other/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_quotation_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'other')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                repair.quotation_path = f"/static/uploads/other/{filename}"
            
            # バージョンを更新
            repair.increment_version()
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='other_repair',
                entity_id=id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'その他修繕履歴 ID:{id} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('修繕履歴が正常に更新されました。', 'success')
            return redirect(url_for('repair.view_other_repair', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/edit_other.html', repair=repair)

@repair_bp.route('/forklift/<int:id>/create_similar', methods=['GET', 'POST'])
def create_similar_forklift_repair(id):
    original_repair = ForkliftRepair.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            repair_date = datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date()
            contractor = request.form['contractor']
            repair_target_type = request.form['repair_target_type']
            repair_item = request.form['repair_item']
            repair_cost = int(request.form['repair_cost'])
            repair_reason = request.form['repair_reason']
            hour_meter = request.form.get('hour_meter')
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # 新しい修繕履歴を作成
            repair = ForkliftRepair(
                forklift_id=original_repair.forklift_id,
                target_management_number=original_repair.target_management_number,
                repair_date=repair_date,
                contractor=contractor,
                repair_target_type=repair_target_type,
                repair_item=repair_item,
                repair_cost=repair_cost,
                repair_reason=repair_reason,
                hour_meter=int(hour_meter) if hour_meter else None,
                notes=notes,
                operator=operator
            )
            
            # ファイルアップロード処理
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_photo_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                repair.photo_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_quotation_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                repair.quotation_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_approval_{approval_document.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                repair.approval_document_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            if 'completion_report' in request.files and request.files['completion_report'].filename:
                completion_report = request.files['completion_report']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_completion_{completion_report.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(repair.forklift_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                completion_report_path = os.path.join(upload_dir, filename)
                completion_report.save(completion_report_path)
                repair.completion_report_path = f"/static/uploads/forklift/{repair.forklift_id}/{filename}"
            
            db.session.add(repair)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='forklift_repair',
                operator=operator,
                details=f'フォークリフト修繕履歴を類似登録 (元ID: {id})'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('類似の修繕履歴が正常に追加されました。', 'success')
            return redirect(url_for('repair.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/edit_forklift.html',
                          repair=original_repair,
                          repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES,
                          repair_reasons=Config.REPAIR_REASON_NAMES,
                          is_similar=True)

@repair_bp.route('/facility/<int:id>/create_similar', methods=['GET', 'POST'])
def create_similar_facility_repair(id):
    original_repair = FacilityRepair.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            repair_date = datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date()
            floor = request.form['floor']
            contractor = request.form['contractor']
            repair_item = request.form['repair_item']
            repair_cost = int(request.form['repair_cost'])
            repair_reason = request.form['repair_reason']
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # 新しい修繕履歴を作成
            repair = FacilityRepair(
                facility_id=original_repair.facility_id,
                target_warehouse_number=original_repair.target_warehouse_number,
                repair_date=repair_date,
                floor=floor,
                contractor=contractor,
                repair_item=repair_item,
                repair_cost=repair_cost,
                repair_reason=repair_reason,
                notes=notes,
                operator=operator
            )
            
            # ファイルアップロード処理
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_photo_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                repair.photo_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_quotation_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                repair.quotation_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_approval_{approval_document.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                repair.approval_document_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            if 'completion_report' in request.files and request.files['completion_report'].filename:
                completion_report = request.files['completion_report']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_completion_{completion_report.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(repair.facility_id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                completion_report_path = os.path.join(upload_dir, filename)
                completion_report.save(completion_report_path)
                repair.completion_report_path = f"/static/uploads/facility/{repair.facility_id}/{filename}"
            
            db.session.add(repair)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='facility_repair',
                operator=operator,
                details=f'倉庫施設修繕履歴を類似登録 (元ID: {id})'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('類似の修繕履歴が正常に追加されました。', 'success')
            return redirect(url_for('repair.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/edit_facility.html',
                          repair=original_repair,
                          repair_reasons=Config.REPAIR_REASON_NAMES,
                          is_similar=True)

@repair_bp.route('/forklift/<int:id>/delete', methods=['POST'])
def delete_forklift_repair(id):
    repair = ForkliftRepair.query.get_or_404(id)
    
    try:
        db.session.delete(repair)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='forklift_repair',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'フォークリフト修繕履歴 ID:{id} を削除'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('修繕履歴が正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('repair.index'))

@repair_bp.route('/facility/<int:id>/delete', methods=['POST'])
def delete_facility_repair(id):
    repair = FacilityRepair.query.get_or_404(id)
    
    try:
        db.session.delete(repair)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='facility_repair',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'倉庫施設修繕履歴 ID:{id} を削除'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('修繕履歴が正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('repair.index'))

@repair_bp.route('/other/<int:id>/delete', methods=['POST'])
def delete_other_repair(id):
    repair = OtherRepair.query.get_or_404(id)
    
    try:
        db.session.delete(repair)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='other_repair',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'その他修繕履歴 ID:{id} を削除'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('修繕履歴が正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('repair.index'))