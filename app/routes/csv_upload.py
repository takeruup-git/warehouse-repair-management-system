from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
import os
import pandas as pd
from werkzeug.utils import secure_filename
from app.models import db, AuditLog
from app.models.forklift import Forklift, ForkliftRepair
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from flask_login import login_required, current_user
from datetime import datetime

csv_upload_bp = Blueprint('csv_upload', __name__)

def allowed_file(filename):
    """ファイルの拡張子が許可されているかチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'csv'}

@csv_upload_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_csv():
    """CSVファイルをアップロードして処理する"""
    if request.method == 'POST':
        # ファイルが存在するか確認
        if 'file' not in request.files:
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # ファイル名が空でないか確認
        if file.filename == '':
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        # ファイル形式が正しいか確認
        if file and allowed_file(file.filename):
            # ファイル名を安全に保存
            filename = secure_filename(file.filename)
            
            # アップロードタイプを取得
            upload_type = request.form.get('upload_type')
            
            # 一時的にファイルを保存
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', filename)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            file.save(temp_path)
            
            try:
                # CSVファイルを読み込む
                df = pd.read_csv(temp_path, encoding='utf-8')
                
                # アップロードタイプに応じた処理
                if upload_type == 'forklift':
                    result = process_forklift_csv(df)
                elif upload_type == 'facility':
                    result = process_facility_csv(df)
                elif upload_type == 'repair':
                    result = process_repair_csv(df)
                else:
                    flash('無効なアップロードタイプです', 'danger')
                    return redirect(request.url)
                
                # 処理結果に応じたメッセージを表示
                if result['success']:
                    flash(f"{result['count']}件のデータを正常にインポートしました", 'success')
                else:
                    error_message = f"インポート中にエラーが発生しました: {result['error']}"
                    if 'fix' in result:
                        error_message += f"<br><br>【対処方法】<br>{result['fix']}"
                    flash(error_message, 'danger')
                
            except Exception as e:
                flash(f"CSVファイルの処理中にエラーが発生しました: {str(e)}", 'danger')
            
            # 一時ファイルを削除
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return redirect(url_for('csv_upload.upload_csv'))
        
        else:
            flash('許可されていないファイル形式です。CSVファイルを選択してください。', 'danger')
            return redirect(request.url)
    
    # GETリクエストの場合、アップロードフォームを表示
    return render_template('csv_upload/upload.html')

def validate_forklift_csv(df):
    """フォークリフトのCSVデータを検証"""
    required_fields = [
        'management_number', 'manufacturer', 'forklift_type', 'power_source', 
        'model', 'serial_number', 'load_capacity', 'manufacture_date', 
        'lift_height', 'warehouse_group', 'warehouse_number', 'floor',
        'asset_type'
    ]
    
    # 必須フィールドの存在確認
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        return {
            'valid': False, 
            'error': f"必須フィールドが不足しています: {', '.join(missing_fields)}",
            'fix': "サンプルCSVをダウンロードして、正しいフィールド名を確認してください。以下のフィールドは必須です：\n" + 
                  "- management_number: フォークリフトの管理番号\n" +
                  "- manufacturer: メーカー名\n" +
                  "- forklift_type: フォークリフトタイプ（reach/counter）\n" +
                  "- power_source: 動力源（battery/diesel/gasoline/lpg）\n" +
                  "- model: 機種\n" +
                  "- serial_number: 機番\n" +
                  "- load_capacity: 積載量（kg）\n" +
                  "- manufacture_date: 製造年月日（YYYY-MM-DD）\n" +
                  "- lift_height: 揚高（mm）\n" +
                  "- warehouse_group: 配置倉庫グループ\n" +
                  "- warehouse_number: 配置倉庫番号\n" +
                  "- floor: 配置倉庫階層\n" +
                  "- asset_type: 資産タイプ（forklift）"
        }
    
    # データ型の検証
    errors = []
    
    # 数値フィールドの検証
    numeric_fields = ['load_capacity', 'lift_height']
    for field in numeric_fields:
        if field in df.columns:
            non_numeric = df[~pd.to_numeric(df[field], errors='coerce').notna()][field]
            if not non_numeric.empty:
                rows = non_numeric.index.tolist()
                errors.append(f"{field}列に数値以外の値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）")
    
    # 日付フィールドの検証
    date_fields = ['manufacture_date', 'acquisition_date']
    for field in date_fields:
        if field in df.columns:
            non_date = df[~pd.to_datetime(df[field], errors='coerce').notna()][field]
            if not non_date.empty:
                rows = non_date.index.tolist()
                errors.append(f"{field}列に日付以外の値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。YYYY-MM-DD形式で入力してください。")
    
    # 列挙型フィールドの検証
    if 'forklift_type' in df.columns:
        invalid_types = df[~df['forklift_type'].isin(['reach', 'counter'])]['forklift_type']
        if not invalid_types.empty:
            rows = invalid_types.index.tolist()
            errors.append(f"forklift_type列に無効な値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。'reach'または'counter'を指定してください。")
    
    if 'power_source' in df.columns:
        invalid_sources = df[~df['power_source'].isin(['battery', 'diesel', 'gasoline', 'lpg'])]['power_source']
        if not invalid_sources.empty:
            rows = invalid_sources.index.tolist()
            errors.append(f"power_source列に無効な値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。'battery'、'diesel'、'gasoline'、または'lpg'を指定してください。")
    
    if 'asset_type' in df.columns:
        invalid_types = df[df['asset_type'] != 'forklift']['asset_type']
        if not invalid_types.empty:
            rows = invalid_types.index.tolist()
            errors.append(f"asset_type列に無効な値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。'forklift'を指定してください。")
    
    if errors:
        return {
            'valid': False,
            'error': "\n".join(errors),
            'fix': "上記のエラーを修正してください。サンプルCSVをダウンロードして参考にしてください。"
        }
    
    return {'valid': True}

def process_forklift_csv(df):
    """フォークリフトのCSVデータを処理"""
    try:
        # データ検証
        validation = validate_forklift_csv(df)
        if not validation['valid']:
            return {'success': False, 'error': validation['error'], 'fix': validation['fix']}
        
        count = 0
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # ヘッダー行を考慮して行番号を+2
            
            # 必須フィールドの値確認
            if pd.isna(row['management_number']):
                errors.append(f"行 {row_num}: 管理番号が空です")
                continue
                
            try:
                # 既存のフォークリフトを検索
                forklift = Forklift.query.filter_by(management_number=row['management_number']).first()
                
                # 新規作成または更新
                if forklift is None:
                    forklift = Forklift()
                    forklift.management_number = row['management_number']
                    
                    # 新規作成時に必須フィールドを設定
                    if 'asset_management_number' not in row or pd.isna(row['asset_management_number']):
                        forklift.asset_management_number = f"FL-{row['management_number']}"
                    else:
                        forklift.asset_management_number = row['asset_management_number']
                    
                    # デフォルト値を設定
                    forklift.department = "物流部"
                    forklift.acquisition_date = datetime.now().date()
                    forklift.useful_life = 8
                    forklift.depreciation_rate = 0.125
                    forklift.acquisition_cost = 0
                    forklift.residual_value = 1
                    forklift.asset_status = "active"
                    forklift.manufacture_date = datetime.now().date()
                    forklift.lift_height = 0
                    forklift.load_capacity = 0
                    forklift.warehouse_group = "デフォルト"
                    forklift.warehouse_number = "不明"
                    forklift.floor = "1F"
                
                # 必須フィールドの設定
                if 'asset_type' not in row or pd.isna(row['asset_type']):
                    forklift.asset_type = "forklift"  # デフォルト値を設定
                else:
                    forklift.asset_type = row['asset_type']
                
                # 各フィールドを更新
                if 'asset_management_number' in row and not pd.isna(row['asset_management_number']):
                    forklift.asset_management_number = row['asset_management_number']
                if 'department' in row and not pd.isna(row['department']):
                    forklift.department = row['department']
                if 'acquisition_date' in row and not pd.isna(row['acquisition_date']):
                    forklift.acquisition_date = pd.to_datetime(row['acquisition_date']).date()
                if 'useful_life' in row and not pd.isna(row['useful_life']):
                    forklift.useful_life = int(row['useful_life'])
                if 'depreciation_rate' in row and not pd.isna(row['depreciation_rate']):
                    forklift.depreciation_rate = float(row['depreciation_rate'])
                if 'acquisition_cost' in row and not pd.isna(row['acquisition_cost']):
                    forklift.acquisition_cost = int(float(row['acquisition_cost']))
                if 'residual_value' in row and not pd.isna(row['residual_value']):
                    forklift.residual_value = int(float(row['residual_value']))
                if 'asset_status' in row and not pd.isna(row['asset_status']):
                    forklift.asset_status = row['asset_status']
                
                if 'model' in row and not pd.isna(row['model']):
                    forklift.model = row['model']
                if 'manufacturer' in row and not pd.isna(row['manufacturer']):
                    forklift.manufacturer = row['manufacturer']
                if 'forklift_type' in row and not pd.isna(row['forklift_type']):
                    forklift.forklift_type = row['forklift_type']
                if 'power_source' in row and not pd.isna(row['power_source']):
                    forklift.power_source = row['power_source']
                if 'serial_number' in row and not pd.isna(row['serial_number']):
                    forklift.serial_number = row['serial_number']
                if 'vehicle_id_number' in row and not pd.isna(row['vehicle_id_number']):
                    forklift.vehicle_id_number = row['vehicle_id_number']
                if 'load_capacity' in row and not pd.isna(row['load_capacity']):
                    forklift.load_capacity = int(float(row['load_capacity']))
                if 'manufacture_date' in row and not pd.isna(row['manufacture_date']):
                    forklift.manufacture_date = pd.to_datetime(row['manufacture_date']).date()
                if 'lift_height' in row and not pd.isna(row['lift_height']):
                    forklift.lift_height = int(float(row['lift_height']))
                if 'warehouse_group' in row and not pd.isna(row['warehouse_group']):
                    forklift.warehouse_group = row['warehouse_group']
                if 'warehouse_number' in row and not pd.isna(row['warehouse_number']):
                    forklift.warehouse_number = row['warehouse_number']
                if 'floor' in row and not pd.isna(row['floor']):
                    forklift.floor = row['floor']
                if 'operator' in row and not pd.isna(row['operator']):
                    forklift.operator = row['operator']
                
                db.session.add(forklift)
                count += 1
                
            except Exception as e:
                errors.append(f"行 {row_num}: {str(e)}")
        
        if errors:
            db.session.rollback()
            error_message = "\n".join(errors)
            return {'success': False, 'error': f"データ処理中にエラーが発生しました:\n{error_message}", 'fix': "エラーメッセージを確認し、CSVファイルを修正してください。"}
        
        db.session.commit()
        return {'success': True, 'count': count}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e), 'fix': "CSVファイルの形式を確認し、サンプルCSVをダウンロードして参考にしてください。"}

def validate_facility_csv(df):
    """倉庫施設のCSVデータを検証"""
    required_fields = [
        'warehouse_number', 'construction_date', 'main_structure', 
        'ownership_type', 'floor_count', 'asset_type'
    ]
    
    # 必須フィールドの存在確認
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        return {
            'valid': False, 
            'error': f"必須フィールドが不足しています: {', '.join(missing_fields)}",
            'fix': "サンプルCSVをダウンロードして、正しいフィールド名を確認してください。以下のフィールドは必須です：\n" + 
                  "- warehouse_number: 倉庫番号\n" +
                  "- construction_date: 建築年月日（YYYY-MM-DD）\n" +
                  "- main_structure: 主要構造（鉄骨造、鉄筋コンクリート造など）\n" +
                  "- ownership_type: 所有形態（owned/leased）\n" +
                  "- floor_count: 階層数\n" +
                  "- asset_type: 資産タイプ（facility）"
        }
    
    # データ型の検証
    errors = []
    
    # 数値フィールドの検証
    numeric_fields = ['floor_count', 'acquisition_cost', 'useful_life']
    for field in numeric_fields:
        if field in df.columns:
            non_numeric = df[~pd.to_numeric(df[field], errors='coerce').notna()][field]
            if not non_numeric.empty:
                rows = non_numeric.index.tolist()
                errors.append(f"{field}列に数値以外の値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）")
    
    # 日付フィールドの検証
    date_fields = ['construction_date', 'acquisition_date']
    for field in date_fields:
        if field in df.columns:
            non_date = df[~pd.to_datetime(df[field], errors='coerce').notna()][field]
            if not non_date.empty:
                rows = non_date.index.tolist()
                errors.append(f"{field}列に日付以外の値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。YYYY-MM-DD形式で入力してください。")
    
    # 列挙型フィールドの検証
    if 'ownership_type' in df.columns:
        invalid_types = df[~df['ownership_type'].isin(['owned', 'leased'])]['ownership_type']
        if not invalid_types.empty:
            rows = invalid_types.index.tolist()
            errors.append(f"ownership_type列に無効な値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。'owned'または'leased'を指定してください。")
    
    if 'asset_type' in df.columns:
        invalid_types = df[df['asset_type'] != 'facility']['asset_type']
        if not invalid_types.empty:
            rows = invalid_types.index.tolist()
            errors.append(f"asset_type列に無効な値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。'facility'を指定してください。")
    
    if errors:
        return {
            'valid': False,
            'error': "\n".join(errors),
            'fix': "上記のエラーを修正してください。サンプルCSVをダウンロードして参考にしてください。"
        }
    
    return {'valid': True}

def process_facility_csv(df):
    """倉庫施設のCSVデータを処理"""
    try:
        # データ検証
        validation = validate_facility_csv(df)
        if not validation['valid']:
            return {'success': False, 'error': validation['error'], 'fix': validation['fix']}
        
        count = 0
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # ヘッダー行を考慮して行番号を+2
            
            # 必須フィールドの値確認
            if pd.isna(row['warehouse_number']):
                errors.append(f"行 {row_num}: 倉庫番号が空です")
                continue
                
            try:
                # 既存の施設を検索
                facility = Facility.query.filter_by(warehouse_number=row['warehouse_number']).first()
                
                # 新規作成または更新
                if facility is None:
                    facility = Facility()
                    facility.warehouse_number = row['warehouse_number']
                    
                    # 新規作成時に必須フィールドを設定
                    if 'asset_management_number' not in row or pd.isna(row['asset_management_number']):
                        facility.asset_management_number = f"WH-{row['warehouse_number']}"
                    else:
                        facility.asset_management_number = row['asset_management_number']
                    
                    # デフォルト値を設定
                    facility.department = "物流部"
                    facility.acquisition_date = datetime.now().date()
                    facility.useful_life = 30
                    facility.depreciation_rate = 0.033
                    facility.acquisition_cost = 0
                    facility.residual_value = 1
                    facility.asset_status = "active"
                    facility.construction_date = datetime.now().date()
                    facility.main_structure = "不明"
                    facility.ownership_type = "owned"
                    facility.floor_count = 1
                
                # 必須フィールドの設定
                if 'asset_type' not in row or pd.isna(row['asset_type']):
                    facility.asset_type = "facility"  # デフォルト値を設定
                else:
                    facility.asset_type = row['asset_type']
                
                # 各フィールドを更新
                if 'asset_management_number' in row and not pd.isna(row['asset_management_number']):
                    facility.asset_management_number = row['asset_management_number']
                if 'department' in row and not pd.isna(row['department']):
                    facility.department = row['department']
                if 'acquisition_date' in row and not pd.isna(row['acquisition_date']):
                    facility.acquisition_date = pd.to_datetime(row['acquisition_date']).date()
                if 'useful_life' in row and not pd.isna(row['useful_life']):
                    facility.useful_life = int(row['useful_life'])
                if 'depreciation_rate' in row and not pd.isna(row['depreciation_rate']):
                    facility.depreciation_rate = float(row['depreciation_rate'])
                if 'acquisition_cost' in row and not pd.isna(row['acquisition_cost']):
                    facility.acquisition_cost = int(float(row['acquisition_cost']))
                if 'residual_value' in row and not pd.isna(row['residual_value']):
                    facility.residual_value = int(float(row['residual_value']))
                if 'asset_status' in row and not pd.isna(row['asset_status']):
                    facility.asset_status = row['asset_status']
                
                if 'construction_date' in row and not pd.isna(row['construction_date']):
                    facility.construction_date = pd.to_datetime(row['construction_date']).date()
                if 'main_structure' in row and not pd.isna(row['main_structure']):
                    facility.main_structure = row['main_structure']
                if 'ownership_type' in row and not pd.isna(row['ownership_type']):
                    facility.ownership_type = row['ownership_type']
                if 'floor_count' in row and not pd.isna(row['floor_count']):
                    facility.floor_count = int(row['floor_count'])
                
                db.session.add(facility)
                count += 1
                
            except Exception as e:
                errors.append(f"行 {row_num}: {str(e)}")
        
        if errors:
            db.session.rollback()
            error_message = "\n".join(errors)
            return {'success': False, 'error': f"データ処理中にエラーが発生しました:\n{error_message}", 'fix': "エラーメッセージを確認し、CSVファイルを修正してください。"}
        
        db.session.commit()
        return {'success': True, 'count': count}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e), 'fix': "CSVファイルの形式を確認し、サンプルCSVをダウンロードして参考にしてください。"}



def process_repair_csv(df):
    """修繕履歴のCSVデータを処理"""
    try:
        # データ検証
        validation = validate_repair_csv(df)
        if not validation['valid']:
            return {'success': False, 'error': validation['error'], 'fix': validation['fix']}
        
        count = 0
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # ヘッダー行を考慮して行番号を+2
            
            # 必須フィールドの値確認
            if ('target_name' not in row or pd.isna(row['target_name'])) and \
               ('management_number' not in row or pd.isna(row['management_number'])) and \
               ('warehouse_number' not in row or pd.isna(row['warehouse_number'])):
                errors.append(f"行 {row_num}: 修繕対象(management_number, warehouse_number, target_name)が指定されていません")
                continue
                
            if 'repair_date' not in row or pd.isna(row['repair_date']):
                errors.append(f"行 {row_num}: 修繕日が空です")
                continue
                
            try:
                # 対象の種類を判断
                target_type = None
                target_id = None
                target_name = None
                
                # フォークリフトの修繕
                if 'management_number' in row and not pd.isna(row['management_number']):
                    forklift = Forklift.query.filter_by(management_number=row['management_number']).first()
                    if forklift:
                        target_type = 'forklift'
                        target_id = forklift.id
                        target_name = forklift.management_number
                        
                        # フォークリフト修繕を作成
                        repair = ForkliftRepair()
                        repair.forklift_id = forklift.id
                        repair.target_management_number = forklift.management_number
                        repair.repair_date = pd.to_datetime(row['repair_date']).date()
                        
                        if 'contractor' in row and not pd.isna(row['contractor']):
                            repair.contractor = row['contractor']
                        else:
                            repair.contractor = '不明'
                        
                        if 'repair_target_type' in row and not pd.isna(row['repair_target_type']):
                            repair.repair_target_type = row['repair_target_type']
                        else:
                            repair.repair_target_type = 'other'
                        
                        if 'repair_item' in row and not pd.isna(row['repair_item']):
                            repair.repair_item = row['repair_item']
                        else:
                            repair.repair_item = '不明'
                        
                        if 'repair_cost' in row and not pd.isna(row['repair_cost']):
                            repair.repair_cost = int(float(row['repair_cost']))
                        else:
                            repair.repair_cost = 0
                        
                        if 'repair_reason' in row and not pd.isna(row['repair_reason']):
                            repair.repair_reason = row['repair_reason']
                        else:
                            repair.repair_reason = 'other'
                        
                        if 'hour_meter' in row and not pd.isna(row['hour_meter']):
                            repair.hour_meter = int(float(row['hour_meter']))
                        
                        if 'notes' in row and not pd.isna(row['notes']):
                            repair.notes = row['notes']
                        
                        if 'operator' in row and not pd.isna(row['operator']):
                            repair.operator = row['operator']
                        else:
                            repair.operator = 'システム'
                        
                        db.session.add(repair)
                        count += 1
                        continue
                    else:
                        errors.append(f"行 {row_num}: 管理番号 {row['management_number']} のフォークリフトが見つかりません")
            
                # 倉庫施設の修繕
                if 'warehouse_number' in row and not pd.isna(row['warehouse_number']):
                    facility = Facility.query.filter_by(warehouse_number=row['warehouse_number']).first()
                    if facility:
                        target_type = 'facility'
                        target_id = facility.id
                        target_name = facility.warehouse_number
                        
                        # 倉庫施設修繕を作成
                        repair = FacilityRepair()
                        repair.facility_id = facility.id
                        repair.target_warehouse_number = facility.warehouse_number
                        repair.repair_date = pd.to_datetime(row['repair_date']).date()
                        
                        if 'floor' in row and not pd.isna(row['floor']):
                            repair.floor = row['floor']
                        else:
                            repair.floor = '1F'
                        
                        if 'contractor' in row and not pd.isna(row['contractor']):
                            repair.contractor = row['contractor']
                        else:
                            repair.contractor = '不明'
                        
                        if 'repair_target_type' in row and not pd.isna(row['repair_target_type']):
                            repair.repair_target_type = row['repair_target_type']
                        else:
                            repair.repair_target_type = 'other'
                        
                        if 'repair_item' in row and not pd.isna(row['repair_item']):
                            repair.repair_item = row['repair_item']
                        else:
                            repair.repair_item = '不明'
                        
                        if 'repair_cost' in row and not pd.isna(row['repair_cost']):
                            repair.repair_cost = int(float(row['repair_cost']))
                        else:
                            repair.repair_cost = 0
                        
                        if 'repair_reason' in row and not pd.isna(row['repair_reason']):
                            repair.repair_reason = row['repair_reason']
                        else:
                            repair.repair_reason = 'other'
                        
                        if 'notes' in row and not pd.isna(row['notes']):
                            repair.notes = row['notes']
                        
                        if 'operator' in row and not pd.isna(row['operator']):
                            repair.operator = row['operator']
                        else:
                            repair.operator = 'システム'
                        
                        db.session.add(repair)
                        count += 1
                        continue
                    else:
                        errors.append(f"行 {row_num}: 倉庫番号 {row['warehouse_number']} の施設が見つかりません")
            
                # その他の修繕
                if 'target_name' in row and not pd.isna(row['target_name']):
                    repair = OtherRepair()
                    repair.target_name = row['target_name']
                    repair.repair_date = pd.to_datetime(row['repair_date']).date()
                    
                    if 'category' in row and not pd.isna(row['category']):
                        repair.category = row['category']
                    else:
                        repair.category = 'その他'
                        
                    if 'repair_cost' in row and not pd.isna(row['repair_cost']):
                        repair.repair_cost = int(float(row['repair_cost']))
                    else:
                        repair.repair_cost = 0
                        
                    if 'contractor' in row and not pd.isna(row['contractor']):
                        repair.contractor = row['contractor']
                    else:
                        repair.contractor = '不明'
                        
                    if 'notes' in row and not pd.isna(row['notes']):
                        repair.notes = row['notes']
                        
                    if 'operator' in row and not pd.isna(row['operator']):
                        repair.operator = row['operator']
                    else:
                        repair.operator = 'システム'
                    
                    db.session.add(repair)
                    count += 1
                    continue
                
                # 対象が特定できない場合
                errors.append(f"行 {row_num}: 修繕対象が特定できません。management_number、warehouse_number、またはtarget_nameを指定してください。")
            
            except Exception as e:
                errors.append(f"行 {row_num}: {str(e)}")
        
        if errors:
            db.session.rollback()
            error_message = "\n".join(errors)
            return {'success': False, 'error': f"データ処理中にエラーが発生しました:\n{error_message}", 'fix': "エラーメッセージを確認し、CSVファイルを修正してください。"}
        
        db.session.commit()
        return {'success': True, 'count': count}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e), 'fix': "CSVファイルの形式を確認し、サンプルCSVをダウンロードして参考にしてください。"}

def validate_repair_csv(df):
    """修繕履歴のCSVデータを検証"""
    required_fields = [
        'repair_date', 'repair_item',
        'repair_cost', 'contractor', 'repair_reason', 'operator'
    ]

    # 必須フィールドの存在確認
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        return {
            'valid': False,
            'error': f"必須フィールドが不足しています: {', '.join(missing_fields)}",
            'fix': "サンプルCSVをダウンロードして、正しいフィールド名を確認してください。以下のフィールドは必須です：\n" + 
                  "- repair_date: 修繕日（YYYY-MM-DD）\n" +
                  "- repair_item: 修繕項目\n" +
                  "- repair_cost: 修繕費用（円）\n" +
                  "- contractor: 業者\n" +
                  "- repair_reason: 修繕理由（wear/damage/malfunction/scheduled/other）\n" +
                  "- operator: 作業者\n\n" +
                  "また、以下のいずれかのフィールドも必要です：\n" +
                  "- management_number: フォークリフト管理番号\n" +
                  "- warehouse_number: 倉庫番号\n" +
                  "- target_name: その他修繕対象名"
        }

    # 識別フィールドの存在確認
    if 'management_number' not in df.columns and 'warehouse_number' not in df.columns and 'target_name' not in df.columns:
        return {
            'valid': False,
            'error': "識別フィールド(management_number, warehouse_number, target_name)のいずれかが必要です",
            'fix': "CSVファイルに少なくとも1つの識別フィールド（management_number、warehouse_number、またはtarget_name）を追加してください。"
        }
    
    # データ型の検証
    errors = []
    
    # 数値フィールドの検証
    numeric_fields = ['repair_cost', 'hour_meter']
    for field in numeric_fields:
        if field in df.columns and not df[field].isna().all():
            non_numeric = df[~pd.to_numeric(df[field], errors='coerce').notna() & ~df[field].isna()][field]
            if not non_numeric.empty:
                rows = non_numeric.index.tolist()
                errors.append(f"{field}列に数値以外の値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）")
    
    # 日付フィールドの検証
    date_fields = ['repair_date']
    for field in date_fields:
        if field in df.columns:
            non_date = df[~pd.to_datetime(df[field], errors='coerce').notna()][field]
            if not non_date.empty:
                rows = non_date.index.tolist()
                errors.append(f"{field}列に日付以外の値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。YYYY-MM-DD形式で入力してください。")
    
    # 列挙型フィールドの検証
    if 'repair_reason' in df.columns:
        valid_reasons = ['wear', 'damage', 'malfunction', 'scheduled', 'other']
        invalid_reasons = df[~df['repair_reason'].isin(valid_reasons) & ~df['repair_reason'].isna()]['repair_reason']
        if not invalid_reasons.empty:
            rows = invalid_reasons.index.tolist()
            errors.append(f"repair_reason列に無効な値があります（行: {', '.join(map(lambda x: str(x+2), rows))}）。{', '.join(valid_reasons)}のいずれかを指定してください。")
    
    if errors:
        return {
            'valid': False,
            'error': "\n".join(errors),
            'fix': "上記のエラーを修正してください。サンプルCSVをダウンロードして参考にしてください。"
        }

    return {'valid': True}
