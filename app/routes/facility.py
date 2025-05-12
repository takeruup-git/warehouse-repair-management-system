from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app.models import db, AuditLog
from app.models.facility import Facility, FacilityRepair
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app.utils.file_utils import secure_filename_with_japanese
from sqlalchemy.exc import IntegrityError
from config import Config

facility_bp = Blueprint('facility', __name__)

@facility_bp.route('/')
def index():
    # 倉庫施設一覧を取得
    facilities = Facility.query.all()
    return render_template('facility/index.html', facilities=facilities)

@facility_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            asset_management_number = request.form['asset_management_number']
            department = request.form['department']
            acquisition_date = datetime.strptime(request.form['acquisition_date'], '%Y-%m-%d').date()
            useful_life = int(request.form['useful_life'])
            depreciation_rate = float(request.form['depreciation_rate'])
            acquisition_cost = int(request.form['acquisition_cost'])
            residual_value = int(request.form['residual_value'])
            asset_status = request.form['asset_status']
            
            warehouse_number = request.form['warehouse_number']
            construction_date = datetime.strptime(request.form['construction_date'], '%Y-%m-%d').date()
            main_structure = request.form['main_structure']
            ownership_type = request.form['ownership_type']
            floor_count = int(request.form['floor_count'])
            
            # 新しい倉庫施設を作成
            facility = Facility(
                asset_management_number=asset_management_number,
                department=department,
                asset_type='facility',
                acquisition_date=acquisition_date,
                useful_life=useful_life,
                depreciation_rate=depreciation_rate,
                acquisition_cost=acquisition_cost,
                residual_value=residual_value,
                asset_status=asset_status,
                warehouse_number=warehouse_number,
                construction_date=construction_date,
                main_structure=main_structure,
                ownership_type=ownership_type,
                floor_count=floor_count
            )
            
            db.session.add(facility)
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='facility',
                entity_id=facility.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'倉庫施設 {warehouse_number} を登録'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('倉庫施設が正常に登録されました。', 'success')
            return redirect(url_for('facility.index'))
            
        except IntegrityError:
            db.session.rollback()
            flash('資産管理番号または倉庫番号が既に使用されています。', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('facility/create.html',
                          ownership_types=Config.OWNERSHIP_TYPE_NAMES,
                          asset_statuses=Config.ASSET_STATUS_NAMES)

@facility_bp.route('/<int:id>')
def view(id):
    facility = Facility.query.get_or_404(id)
    repairs = FacilityRepair.query.filter_by(facility_id=id).order_by(FacilityRepair.repair_date.desc()).all()
    
    return render_template('facility/view.html',
                          facility=facility,
                          repairs=repairs)

@facility_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    facility = Facility.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # バージョンチェック（楽観的ロック）
            form_version = int(request.form['version'])
            if form_version != facility.version:
                flash('この倉庫施設は他のユーザーによって更新されました。最新の情報を確認してください。', 'danger')
                return redirect(url_for('facility.edit', id=id))
            
            # フォームからデータを取得して更新
            facility.department = request.form['department']
            facility.acquisition_date = datetime.strptime(request.form['acquisition_date'], '%Y-%m-%d').date()
            facility.useful_life = int(request.form['useful_life'])
            facility.depreciation_rate = float(request.form['depreciation_rate'])
            facility.acquisition_cost = int(request.form['acquisition_cost'])
            facility.residual_value = int(request.form['residual_value'])
            facility.asset_status = request.form['asset_status']
            
            facility.construction_date = datetime.strptime(request.form['construction_date'], '%Y-%m-%d').date()
            facility.main_structure = request.form['main_structure']
            facility.ownership_type = request.form['ownership_type']
            facility.floor_count = int(request.form['floor_count'])
            
            # バージョンを更新
            facility.increment_version()
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='facility',
                entity_id=facility.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'倉庫施設 {facility.warehouse_number} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('倉庫施設が正常に更新されました。', 'success')
            return redirect(url_for('facility.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('facility/edit.html',
                          facility=facility,
                          ownership_types=Config.OWNERSHIP_TYPE_NAMES,
                          asset_statuses=Config.ASSET_STATUS_NAMES)

@facility_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    facility = Facility.query.get_or_404(id)
    warehouse_number = facility.warehouse_number
    
    try:
        db.session.delete(facility)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='facility',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'倉庫施設 {warehouse_number} を削除'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('倉庫施設が正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('facility.index'))

@facility_bp.route('/<int:id>/add_repair', methods=['GET', 'POST'])
def add_repair(id):
    facility = Facility.query.get_or_404(id)
    
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
            
            # ファイルアップロード処理
            photo_path = None
            quotation_path = None
            approval_document_path = None
            completion_report_path = None
            
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename_with_japanese(photo.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'photo'
                unique_dir = os.path.join('facility', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                photo_path = f"/static/uploads/{unique_dir}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename_with_japanese(quotation.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'quotation'
                unique_dir = os.path.join('facility', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                quotation_path = f"/static/uploads/{unique_dir}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename_with_japanese(approval_document.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'approval'
                unique_dir = os.path.join('facility', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                approval_document_path = f"/static/uploads/{unique_dir}/{filename}"
            
            if 'completion_report' in request.files and request.files['completion_report'].filename:
                completion_report = request.files['completion_report']
                filename = secure_filename_with_japanese(completion_report.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'completion'
                unique_dir = os.path.join('facility', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                completion_report_path = os.path.join(upload_dir, filename)
                completion_report.save(completion_report_path)
                completion_report_path = f"/static/uploads/{unique_dir}/{filename}"
            
            # 修繕履歴を作成
            repair = FacilityRepair(
                repair_date=repair_date,
                facility_id=id,
                target_warehouse_number=facility.warehouse_number,
                floor=floor,
                contractor=contractor,
                repair_item=repair_item,
                repair_cost=repair_cost,
                repair_reason=repair_reason,
                photo_path=photo_path,
                quotation_path=quotation_path,
                approval_document_path=approval_document_path,
                completion_report_path=completion_report_path,
                notes=notes,
                operator=operator
            )
            
            db.session.add(repair)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='facility_repair',
                entity_id=id,
                operator=operator,
                details=f'倉庫施設 {facility.warehouse_number} の修繕履歴を追加'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('修繕履歴が正常に追加されました。', 'success')
            return redirect(url_for('facility.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('facility/add_repair.html',
                          facility=facility,
                          repair_reasons=Config.REPAIR_REASON_NAMES)