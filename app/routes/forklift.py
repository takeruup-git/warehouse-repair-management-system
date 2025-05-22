from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from app.models import db, AuditLog
from app.models.forklift import Forklift, ForkliftRepair, ForkliftPrediction
from app.models.master import Manufacturer, WarehouseGroup, MasterItem
from app.models.file import FileMetadata
from datetime import datetime
import os
import glob
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from config import Config
from app.utils.excel_generator import generate_inspection_format

forklift_bp = Blueprint('forklift', __name__)

@forklift_bp.route('/')
def index():
    # フォークリフト一覧を取得
    forklifts = Forklift.query.all()
    return render_template('forklift/index.html', forklifts=forklifts)

# 画像閲覧機能は詳細画面に統合したため削除

@forklift_bp.route('/generate_inspection_format')
def generate_inspection_format_route():
    """
    稼働中のフォークリフト全てに対する定期自主検査記録表のExcelファイルを生成する
    """
    try:
        # 全フォークリフトを取得
        forklifts = Forklift.query.filter_by(asset_status='active').all()
        
        if not forklifts:
            flash('稼働中のフォークリフトが見つかりません。', 'warning')
            return redirect(url_for('forklift.index'))
        
        # Excelファイルを生成
        file_path = generate_inspection_format(forklifts)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='generate',
            entity_type='inspection_format',
            operator=request.args.get('operator_name', 'システム'),
            details=f'定期自主検査記録表フォーマットを生成（{len(forklifts)}台）'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        # 成功メッセージを表示
        flash(f'定期自主検査記録表フォーマットが正常に生成されました。（{len(forklifts)}台）', 'success')
        
        # ファイルのフルパスを取得
        full_path = os.path.join(current_app.root_path, file_path)
        
        # ファイルをダウンロード
        return send_file(
            full_path,
            as_attachment=True,
            download_name=f'forklift_inspection_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'フォーマット生成中にエラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('forklift.index'))

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
            vehicle_id_number = request.form.get('vehicle_id_number', '')
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
                vehicle_id_number=vehicle_id_number if vehicle_id_number else None,
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
    
    # マスターアイテムからデータを取得
    forklift_types_db = MasterItem.query.filter_by(category='forklift_type', is_active=True).order_by(MasterItem.sort_order).all()
    power_sources_db = MasterItem.query.filter_by(category='power_source', is_active=True).order_by(MasterItem.sort_order).all()
    asset_statuses_db = MasterItem.query.filter_by(category='asset_status', is_active=True).order_by(MasterItem.sort_order).all()
    
    # マスターアイテムがない場合は設定ファイルから取得
    forklift_types = {item.key: item.value for item in forklift_types_db} if forklift_types_db else Config.FORKLIFT_TYPE_NAMES
    power_sources = {item.key: item.value for item in power_sources_db} if power_sources_db else Config.POWER_SOURCE_NAMES
    asset_statuses = {item.key: item.value for item in asset_statuses_db} if asset_statuses_db else Config.ASSET_STATUS_NAMES
    
    # 追加のマスターデータ
    departments = Config.DEPARTMENT_NAMES
    warehouse_numbers = Config.WAREHOUSE_NUMBER_NAMES
    floors = Config.FLOOR_NAMES
    operators = Config.OPERATOR_NAMES
    
    return render_template('forklift/create.html',
                          manufacturers=manufacturers,
                          warehouse_groups=warehouse_groups,
                          forklift_types=forklift_types,
                          power_sources=power_sources,
                          asset_statuses=asset_statuses,
                          departments=departments,
                          warehouse_numbers=warehouse_numbers,
                          floors=floors,
                          operators=operators)

@forklift_bp.route('/<int:id>')
def view(id):
    try:
        forklift = Forklift.query.get_or_404(id)
        repairs = ForkliftRepair.query.filter_by(forklift_id=id).order_by(ForkliftRepair.repair_date.desc()).all()
        
        # 予測データがない場合は新規作成
        prediction = ForkliftPrediction.query.filter_by(forklift_id=id).first()
        if not prediction:
            prediction = ForkliftPrediction(forklift_id=id)
            db.session.add(prediction)
            db.session.commit()
        
        return render_template('forklift/view.html',
                              forklift=forklift,
                              repairs=repairs,
                              prediction=prediction)
    except Exception as e:
        current_app.logger.error(f"フォークリフト詳細表示エラー: {str(e)}")
        flash(f"フォークリフト詳細の表示中にエラーが発生しました: {str(e)}", "danger")
        return redirect(url_for('forklift.index'))

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
            forklift.vehicle_id_number = request.form.get('vehicle_id_number', '') or None
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
                filename = secure_filename(photo.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'photo'
                unique_dir = os.path.join('forklift', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                photo_path = f"/static/uploads/{unique_dir}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(quotation.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'quotation'
                unique_dir = os.path.join('forklift', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                quotation_path = f"/static/uploads/{unique_dir}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(approval_document.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'approval'
                unique_dir = os.path.join('forklift', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                approval_document_path = f"/static/uploads/{unique_dir}/{filename}"
            
            if 'completion_report' in request.files and request.files['completion_report'].filename:
                completion_report = request.files['completion_report']
                filename = secure_filename(completion_report.filename)
                
                # 日付とタイプを含むサブディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_type = 'completion'
                unique_dir = os.path.join('forklift', str(id), f"{date_str}_{file_type}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                completion_report_path = os.path.join(upload_dir, filename)
                completion_report.save(completion_report_path)
                completion_report_path = f"/static/uploads/{unique_dir}/{filename}"
            
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
            
            elif repair_target_type in ['drive_tire', 'caster_tire', 'other_tire']:
                prediction = ForkliftPrediction.query.filter_by(forklift_id=id).first()
                if not prediction:
                    prediction = ForkliftPrediction(forklift_id=id)
                    db.session.add(prediction)
                
                # 次回交換予測日を設定
                component = repair_target_type
                lifespan = db.session.query(EquipmentLifespan).filter_by(
                    equipment_type='forklift', component=component
                ).first()
                
                if lifespan:
                    months_to_add = lifespan.expected_lifespan
                else:
                    # デフォルト値
                    if component == 'drive_tire':
                        months_to_add = 24
                    elif component == 'caster_tire':
                        months_to_add = 18
                    else:  # other_tire
                        months_to_add = 20
                
                next_date = repair_date.replace(year=repair_date.year + (months_to_add // 12))
                if months_to_add % 12 > 0:
                    # 月を加算（簡易的な実装）
                    month = repair_date.month + (months_to_add % 12)
                    if month > 12:
                        next_date = next_date.replace(year=next_date.year + 1, month=month - 12)
                    else:
                        next_date = next_date.replace(month=month)
                
                # 後方互換性のために古いフィールドも更新
                prediction.tire_replacement_date = repair_date
                prediction.tire_type = 'drive' if repair_target_type == 'drive_tire' else ('caster' if repair_target_type == 'caster_tire' else 'other')
                prediction.next_tire_replacement_date = next_date
                
                # 新しいフィールドを更新
                if repair_target_type == 'drive_tire':
                    prediction.drive_tire_replacement_date = repair_date
                    prediction.next_drive_tire_replacement_date = next_date
                elif repair_target_type == 'caster_tire':
                    prediction.caster_tire_replacement_date = repair_date
                    prediction.next_caster_tire_replacement_date = next_date
                elif repair_target_type == 'other_tire':
                    prediction.other_tire_replacement_date = repair_date
                    prediction.next_other_tire_replacement_date = next_date
                    # その他タイヤの種類を記録（フォームから取得）
                    other_tire_type = request.form.get('other_tire_type')
                    if other_tire_type:
                        prediction.other_tire_type = other_tire_type
            
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