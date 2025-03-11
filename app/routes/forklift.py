from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app.models import db, AuditLog
from app.models.forklift import Forklift, ForkliftRepair, ForkliftPrediction
from app.models.master import Manufacturer, WarehouseGroup
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from config import Config

forklift_bp = Blueprint('forklift', __name__)

@forklift_bp.route('/')
def index():
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    return render_template('forklift/index.html', forklifts=forklifts)

@forklift_bp.route('/create', methods=['GET', 'POST'])
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
            
            management_number = request.form['management_number']
            manufacturer = request.form['manufacturer']
            forklift_type = request.form['forklift_type']
            power_source = request.form['power_source']
            model = request.form['model']
            serial_number = request.form['serial_number']
            load_capacity = int(request.form['load_capacity'])
            manufacture_date = datetime.strptime(request.form['manufacture_date'], '%Y-%m-%d').date()
            lift_height = int(request.form['lift_height'])
            warehouse_group = request.form['warehouse_group']
            warehouse_number = request.form['warehouse_number']
            floor = request.form['floor']
            operator = request.form['operator']
            
            # 新しいフォークリフトを作成
            forklift = Forklift(
                asset_management_number=asset_management_number,
                department=department,
                asset_type='forklift',
                acquisition_date=acquisition_date,
                useful_life=useful_life,
                depreciation_rate=depreciation_rate,
                acquisition_cost=acquisition_cost,
                residual_value=residual_value,
                asset_status=asset_status,
                management_number=management_number,
                manufacturer=manufacturer,
                forklift_type=forklift_type,
                power_source=power_source,
                model=model,
                serial_number=serial_number,
                load_capacity=load_capacity,
                manufacture_date=manufacture_date,
                lift_height=lift_height,
                warehouse_group=warehouse_group,
                warehouse_number=warehouse_number,
                floor=floor,
                operator=operator
            )
            
            db.session.add(forklift)
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='forklift',
                entity_id=forklift.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'フォークリフト {management_number} を登録'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('フォークリフトが正常に登録されました。', 'success')
            return redirect(url_for('forklift.index'))
            
        except IntegrityError:
            db.session.rollback()
            flash('資産管理番号または管理番号が既に使用されています。', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # マスターデータを取得
    manufacturers = Manufacturer.query.filter_by(is_active=True).all()
    warehouse_groups = WarehouseGroup.query.filter_by(is_active=True).all()
    
    return render_template('forklift/create.html',
                          manufacturers=manufacturers,
                          warehouse_groups=warehouse_groups,
                          forklift_types=Config.FORKLIFT_TYPE_NAMES,
                          power_sources=Config.POWER_SOURCE_NAMES,
                          asset_statuses=Config.ASSET_STATUS_NAMES)

@forklift_bp.route('/<int:id>')
def view(id):
    forklift = Forklift.query.get_or_404(id)
    repairs = ForkliftRepair.query.filter_by(forklift_id=id).order_by(ForkliftRepair.repair_date.desc()).all()
    prediction = ForkliftPrediction.query.filter_by(forklift_id=id).first()
    
    return render_template('forklift/view.html',
                          forklift=forklift,
                          repairs=repairs,
                          prediction=prediction)

@forklift_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    forklift = Forklift.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # バージョンチェック（楽観的ロック）
            form_version = int(request.form['version'])
            if form_version != forklift.version:
                flash('このフォークリフトは他のユーザーによって更新されました。最新の情報を確認してください。', 'danger')
                return redirect(url_for('forklift.edit', id=id))
            
            # フォームからデータを取得して更新
            forklift.department = request.form['department']
            forklift.acquisition_date = datetime.strptime(request.form['acquisition_date'], '%Y-%m-%d').date()
            forklift.useful_life = int(request.form['useful_life'])
            forklift.depreciation_rate = float(request.form['depreciation_rate'])
            forklift.acquisition_cost = int(request.form['acquisition_cost'])
            forklift.residual_value = int(request.form['residual_value'])
            forklift.asset_status = request.form['asset_status']
            
            forklift.manufacturer = request.form['manufacturer']
            forklift.forklift_type = request.form['forklift_type']
            forklift.power_source = request.form['power_source']
            forklift.model = request.form['model']
            forklift.serial_number = request.form['serial_number']
            forklift.load_capacity = int(request.form['load_capacity'])
            forklift.manufacture_date = datetime.strptime(request.form['manufacture_date'], '%Y-%m-%d').date()
            forklift.lift_height = int(request.form['lift_height'])
            forklift.warehouse_group = request.form['warehouse_group']
            forklift.warehouse_number = request.form['warehouse_number']
            forklift.floor = request.form['floor']
            forklift.operator = request.form['operator']
            
            # バージョンを更新
            forklift.increment_version()
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='forklift',
                entity_id=forklift.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'フォークリフト {forklift.management_number} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('フォークリフトが正常に更新されました。', 'success')
            return redirect(url_for('forklift.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # マスターデータを取得
    manufacturers = Manufacturer.query.filter_by(is_active=True).all()
    warehouse_groups = WarehouseGroup.query.filter_by(is_active=True).all()
    
    return render_template('forklift/edit.html',
                          forklift=forklift,
                          manufacturers=manufacturers,
                          warehouse_groups=warehouse_groups,
                          forklift_types=Config.FORKLIFT_TYPE_NAMES,
                          power_sources=Config.POWER_SOURCE_NAMES,
                          asset_statuses=Config.ASSET_STATUS_NAMES)

@forklift_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    forklift = Forklift.query.get_or_404(id)
    management_number = forklift.management_number
    
    try:
        db.session.delete(forklift)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='forklift',
            entity_id=id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'フォークリフト {management_number} を削除'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('フォークリフトが正常に削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('forklift.index'))

@forklift_bp.route('/<int:id>/add_repair', methods=['GET', 'POST'])
def add_repair(id):
    forklift = Forklift.query.get_or_404(id)
    
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
            if hour_meter:
                hour_meter = int(hour_meter)
            notes = request.form.get('notes', '')
            operator = request.form['operator_name']
            
            # ファイルアップロード処理
            photo_path = None
            quotation_path = None
            approval_document_path = None
            completion_report_path = None
            
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_photo_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                photo_path = f"/static/uploads/forklift/{id}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_quotation_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                quotation_path = f"/static/uploads/forklift/{id}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_approval_{approval_document.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                approval_document_path = f"/static/uploads/forklift/{id}/{filename}"
            
            if 'completion_report' in request.files and request.files['completion_report'].filename:
                completion_report = request.files['completion_report']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_completion_{completion_report.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                completion_report_path = os.path.join(upload_dir, filename)
                completion_report.save(completion_report_path)
                completion_report_path = f"/static/uploads/forklift/{id}/{filename}"
            
            # 修繕履歴を作成
            repair = ForkliftRepair(
                repair_date=repair_date,
                forklift_id=id,
                target_management_number=forklift.management_number,
                contractor=contractor,
                repair_target_type=repair_target_type,
                repair_item=repair_item,
                repair_cost=repair_cost,
                repair_reason=repair_reason,
                hour_meter=hour_meter,
                photo_path=photo_path,
                quotation_path=quotation_path,
                approval_document_path=approval_document_path,
                completion_report_path=completion_report_path,
                notes=notes,
                operator=operator
            )
            
            db.session.add(repair)
            
            # 修繕予測データの更新
            if repair_target_type == 'battery':
                prediction = ForkliftPrediction.query.filter_by(forklift_id=id).first()
                if not prediction:
                    prediction = ForkliftPrediction(forklift_id=id)
                    db.session.add(prediction)
                
                prediction.battery_replacement_date = repair_date
                
                # 次回交換予測日を設定（3年後）
                lifespan = db.session.query(EquipmentLifespan).filter_by(
                    equipment_type='forklift', component='battery'
                ).first()
                
                if lifespan:
                    months_to_add = lifespan.expected_lifespan
                else:
                    months_to_add = 36  # デフォルト3年
                
                next_date = repair_date.replace(year=repair_date.year + (months_to_add // 12))
                if months_to_add % 12 > 0:
                    # 月を加算（簡易的な実装）
                    month = repair_date.month + (months_to_add % 12)
                    if month > 12:
                        next_date = next_date.replace(year=next_date.year + 1, month=month - 12)
                    else:
                        next_date = next_date.replace(month=month)
                
                prediction.next_battery_replacement_date = next_date
            
            elif repair_target_type in ['drive_tire', 'caster_tire']:
                prediction = ForkliftPrediction.query.filter_by(forklift_id=id).first()
                if not prediction:
                    prediction = ForkliftPrediction(forklift_id=id)
                    db.session.add(prediction)
                
                prediction.tire_replacement_date = repair_date
                prediction.tire_type = 'drive' if repair_target_type == 'drive_tire' else 'caster'
                
                # 次回交換予測日を設定
                component = 'drive_tire' if repair_target_type == 'drive_tire' else 'caster_tire'
                lifespan = db.session.query(EquipmentLifespan).filter_by(
                    equipment_type='forklift', component=component
                ).first()
                
                if lifespan:
                    months_to_add = lifespan.expected_lifespan
                else:
                    months_to_add = 24 if component == 'drive_tire' else 18  # デフォルト
                
                next_date = repair_date.replace(year=repair_date.year + (months_to_add // 12))
                if months_to_add % 12 > 0:
                    # 月を加算（簡易的な実装）
                    month = repair_date.month + (months_to_add % 12)
                    if month > 12:
                        next_date = next_date.replace(year=next_date.year + 1, month=month - 12)
                    else:
                        next_date = next_date.replace(month=month)
                
                prediction.next_tire_replacement_date = next_date
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='forklift_repair',
                entity_id=id,
                operator=operator,
                details=f'フォークリフト {forklift.management_number} の修繕履歴を追加'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('修繕履歴が正常に追加されました。', 'success')
            return redirect(url_for('forklift.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('forklift/add_repair.html',
                          forklift=forklift,
                          repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES,
                          repair_reasons=Config.REPAIR_REASON_NAMES)