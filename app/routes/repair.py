from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app.models import db, AuditLog
from app.models.forklift import Forklift, ForkliftRepair, ForkliftPrediction
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from app.models.master import WarehouseGroup
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config

repair_bp = Blueprint('repair', __name__)

@repair_bp.route('/')
def index():
    # 検索パラメータを取得
    search_type = request.args.get('type', 'all')
    search_keyword = request.args.get('keyword', '')
    search_date_from = request.args.get('date_from', '')
    search_date_to = request.args.get('date_to', '')
    search_reason = request.args.get('reason', '')
    
    # 日付の変換
    date_from = None
    date_to = None
    try:
        if search_date_from:
            date_from = datetime.strptime(search_date_from, '%Y-%m-%d').date()
        if search_date_to:
            date_to = datetime.strptime(search_date_to, '%Y-%m-%d').date()
    except ValueError:
        flash('日付の形式が正しくありません。', 'danger')
    
    # フォークリフト修繕履歴のクエリ
    forklift_query = ForkliftRepair.query
    
    # 検索条件の適用
    if search_keyword:
        forklift_query = forklift_query.filter(
            (ForkliftRepair.repair_item.ilike(f'%{search_keyword}%')) |
            (ForkliftRepair.forklift_management_number.ilike(f'%{search_keyword}%')) |
            (ForkliftRepair.vendor.ilike(f'%{search_keyword}%')) |
            (ForkliftRepair.notes.ilike(f'%{search_keyword}%'))
        )
    
    if date_from:
        forklift_query = forklift_query.filter(ForkliftRepair.repair_date >= date_from)
    if date_to:
        forklift_query = forklift_query.filter(ForkliftRepair.repair_date <= date_to)
    if search_reason:
        forklift_query = forklift_query.filter(ForkliftRepair.repair_reason == search_reason)
    
    # 倉庫施設修繕履歴のクエリ
    facility_query = FacilityRepair.query
    
    # 検索条件の適用
    if search_keyword:
        facility_query = facility_query.filter(
            (FacilityRepair.repair_item.ilike(f'%{search_keyword}%')) |
            (FacilityRepair.facility_name.ilike(f'%{search_keyword}%')) |
            (FacilityRepair.vendor.ilike(f'%{search_keyword}%')) |
            (FacilityRepair.notes.ilike(f'%{search_keyword}%'))
        )
    
    if date_from:
        facility_query = facility_query.filter(FacilityRepair.repair_date >= date_from)
    if date_to:
        facility_query = facility_query.filter(FacilityRepair.repair_date <= date_to)
    if search_reason:
        facility_query = facility_query.filter(FacilityRepair.repair_reason == search_reason)
    
    # その他修繕履歴のクエリ
    other_query = OtherRepair.query
    
    # 検索条件の適用
    if search_keyword:
        other_query = other_query.filter(
            (OtherRepair.repair_item.ilike(f'%{search_keyword}%')) |
            (OtherRepair.repair_target.ilike(f'%{search_keyword}%')) |
            (OtherRepair.vendor.ilike(f'%{search_keyword}%')) |
            (OtherRepair.notes.ilike(f'%{search_keyword}%'))
        )
    
    if date_from:
        other_query = other_query.filter(OtherRepair.repair_date >= date_from)
    if date_to:
        other_query = other_query.filter(OtherRepair.repair_date <= date_to)
    
    # タイプによるフィルタリング
    if search_type == 'forklift':
        facility_query = facility_query.filter(FacilityRepair.id < 0)  # 空のクエリにする
        other_query = other_query.filter(OtherRepair.id < 0)  # 空のクエリにする
    elif search_type == 'facility':
        forklift_query = forklift_query.filter(ForkliftRepair.id < 0)  # 空のクエリにする
        other_query = other_query.filter(OtherRepair.id < 0)  # 空のクエリにする
    elif search_type == 'other':
        forklift_query = forklift_query.filter(ForkliftRepair.id < 0)  # 空のクエリにする
        facility_query = facility_query.filter(FacilityRepair.id < 0)  # 空のクエリにする
    
    # 結果の取得
    forklift_repairs = forklift_query.order_by(ForkliftRepair.repair_date.desc()).all()
    facility_repairs = facility_query.order_by(FacilityRepair.repair_date.desc()).all()
    other_repairs = other_query.order_by(OtherRepair.repair_date.desc()).all()
    
    return render_template('repair/index.html',
                          forklift_repairs=forklift_repairs,
                          facility_repairs=facility_repairs,
                          other_repairs=other_repairs,
                          repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES,
                          repair_reasons=Config.REPAIR_REASON_NAMES,
                          search_type=search_type,
                          search_keyword=search_keyword,
                          search_date_from=search_date_from,
                          search_date_to=search_date_to,
                          search_reason=search_reason)

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

@repair_bp.route('/create')
def create_select():
    """修繕対象選択ページ"""
    return render_template('repair/create_select.html')

@repair_bp.route('/create/forklift')
def create_forklift_repair_select():
    """フォークリフト選択ページ"""
    # 検索パラメータを取得
    search_keyword = request.args.get('keyword', '')
    search_warehouse_group = request.args.get('warehouse_group', '')
    
    # フォークリフトのクエリ
    query = Forklift.query.filter_by(asset_status='active')
    
    # 検索条件の適用
    if search_keyword:
        query = query.filter(
            (Forklift.management_number.ilike(f'%{search_keyword}%')) |
            (Forklift.manufacturer.ilike(f'%{search_keyword}%')) |
            (Forklift.model.ilike(f'%{search_keyword}%'))
        )
    
    if search_warehouse_group:
        query = query.filter(Forklift.warehouse_group == search_warehouse_group)
    
    # 結果の取得
    forklifts = query.order_by(Forklift.management_number).all()
    
    # 倉庫グループの取得
    warehouse_groups = WarehouseGroup.query.filter_by(is_active=True).all()
    
    return render_template('repair/create_forklift_select.html',
                          forklifts=forklifts,
                          warehouse_groups=warehouse_groups,
                          search_keyword=search_keyword,
                          search_warehouse_group=search_warehouse_group)

@repair_bp.route('/create/facility')
def create_facility_repair_select():
    """倉庫施設選択ページ"""
    # 検索パラメータを取得
    search_keyword = request.args.get('keyword', '')
    search_warehouse_group = request.args.get('warehouse_group', '')
    
    # 倉庫施設のクエリ
    query = Facility.query.filter_by(asset_status='active')
    
    # 検索条件の適用
    if search_keyword:
        query = query.filter(
            (Facility.name.ilike(f'%{search_keyword}%')) |
            (Facility.address.ilike(f'%{search_keyword}%'))
        )
    
    if search_warehouse_group:
        query = query.filter(Facility.warehouse_group == search_warehouse_group)
    
    # 結果の取得
    facilities = query.order_by(Facility.name).all()
    
    # 倉庫グループの取得
    warehouse_groups = WarehouseGroup.query.filter_by(is_active=True).all()
    
    return render_template('repair/create_facility_select.html',
                          facilities=facilities,
                          warehouse_groups=warehouse_groups,
                          search_keyword=search_keyword,
                          search_warehouse_group=search_warehouse_group)

@repair_bp.route('/create/forklift/<int:forklift_id>', methods=['GET', 'POST'])
def create_forklift_repair(forklift_id):
    """フォークリフト修繕登録"""
    forklift = Forklift.query.get_or_404(forklift_id)
    
    if request.method == 'POST':
        try:
            # フォームからデータを取得
            repair_date = datetime.strptime(request.form['repair_date'], '%Y-%m-%d').date()
            repair_target_type = request.form['repair_target_type']
            repair_item = request.form['repair_item']
            repair_cost = int(request.form['repair_cost'])
            repair_reason = request.form['repair_reason']
            vendor = request.form['vendor']
            notes = request.form.get('notes', '')
            
            # 修繕履歴を作成
            repair = ForkliftRepair(
                forklift_id=forklift.id,
                forklift_management_number=forklift.management_number,
                repair_date=repair_date,
                repair_target_type=repair_target_type,
                repair_item=repair_item,
                repair_cost=repair_cost,
                repair_reason=repair_reason,
                vendor=vendor,
                notes=notes,
                operator=request.form.get('operator_name', 'システム')
            )
            
            # ファイルアップロード処理
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(forklift.id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                repair.photo_path = f"/static/uploads/forklift/{forklift.id}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(forklift.id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                repair.quotation_path = f"/static/uploads/forklift/{forklift.id}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{approval_document.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'forklift', str(forklift.id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                repair.approval_document_path = f"/static/uploads/forklift/{forklift.id}/{filename}"
            
            db.session.add(repair)
            db.session.commit()
            
            # バッテリーまたはタイヤの交換情報を更新
            if repair_target_type == 'battery':
                # バッテリー交換情報を更新
                prediction = ForkliftPrediction.query.filter_by(forklift_id=forklift.id).first()
                if not prediction:
                    prediction = ForkliftPrediction(forklift_id=forklift.id)
                    db.session.add(prediction)
                
                prediction.battery_replacement_date = repair_date
                # 次回交換予定日は2年後に設定（バッテリーの標準的な寿命を2年と仮定）
                prediction.next_battery_replacement_date = datetime(
                    repair_date.year + 2, repair_date.month, repair_date.day
                ).date()
                prediction.updated_by = request.form.get('operator_name', 'システム')
                db.session.commit()
                
                flash('バッテリー交換情報が自動的に更新されました。', 'info')
            
            elif repair_target_type in ['drive_tire', 'caster_tire']:
                # タイヤ交換情報を更新
                prediction = ForkliftPrediction.query.filter_by(forklift_id=forklift.id).first()
                if not prediction:
                    prediction = ForkliftPrediction(forklift_id=forklift.id)
                    db.session.add(prediction)
                
                prediction.tire_replacement_date = repair_date
                # タイヤタイプを設定
                if repair_target_type == 'drive_tire':
                    prediction.tire_type = 'drive'
                elif repair_target_type == 'caster_tire':
                    prediction.tire_type = 'caster'
                
                # 次回交換予定日は1年後に設定（タイヤの標準的な寿命を1年と仮定）
                prediction.next_tire_replacement_date = datetime(
                    repair_date.year + 1, repair_date.month, repair_date.day
                ).date()
                prediction.updated_by = request.form.get('operator_name', 'システム')
                db.session.commit()
                
                flash('タイヤ交換情報が自動的に更新されました。', 'info')
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='forklift_repair',
                entity_id=repair.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'フォークリフト {forklift.management_number} の修繕履歴を登録'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('フォークリフト修繕履歴が正常に登録されました。', 'success')
            return redirect(url_for('forklift.view', id=forklift.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/create_forklift.html',
                          forklift=forklift,
                          repair_target_types=Config.REPAIR_TARGET_TYPE_NAMES,
                          repair_reasons=Config.REPAIR_REASON_NAMES)

@repair_bp.route('/create/facility/<int:facility_id>', methods=['GET', 'POST'])
def create_facility_repair(facility_id):
    """倉庫施設修繕登録"""
    facility = Facility.query.get_or_404(facility_id)
    
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
            
            # 修繕履歴を作成
            repair = FacilityRepair(
                facility_id=facility.id,
                facility_name=facility.name,
                repair_date=repair_date,
                floor=floor,
                contractor=contractor,
                repair_item=repair_item,
                repair_cost=repair_cost,
                repair_reason=repair_reason,
                notes=notes,
                operator=request.form.get('operator_name', 'システム')
            )
            
            # ファイルアップロード処理
            if 'photo' in request.files and request.files['photo'].filename:
                photo = request.files['photo']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(facility.id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                photo_path = os.path.join(upload_dir, filename)
                photo.save(photo_path)
                repair.photo_path = f"/static/uploads/facility/{facility.id}/{filename}"
            
            if 'quotation' in request.files and request.files['quotation'].filename:
                quotation = request.files['quotation']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{quotation.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(facility.id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                quotation_path = os.path.join(upload_dir, filename)
                quotation.save(quotation_path)
                repair.quotation_path = f"/static/uploads/facility/{facility.id}/{filename}"
            
            if 'approval_document' in request.files and request.files['approval_document'].filename:
                approval_document = request.files['approval_document']
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{approval_document.filename}")
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'facility', str(facility.id))
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                approval_document_path = os.path.join(upload_dir, filename)
                approval_document.save(approval_document_path)
                repair.approval_document_path = f"/static/uploads/facility/{facility.id}/{filename}"
            
            db.session.add(repair)
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='facility_repair',
                entity_id=repair.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'倉庫施設 {facility.name} の修繕履歴を登録'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('倉庫施設修繕履歴が正常に登録されました。', 'success')
            return redirect(url_for('facility.view', id=facility.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return render_template('repair/create_facility.html',
                          facility=facility,
                          repair_reasons=Config.REPAIR_REASON_NAMES)

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