from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
import os
import pandas as pd
from werkzeug.utils import secure_filename
from app.models import db
from app.models.forklift import Forklift
from app.models.facility import Facility
from app.models.other_repair import OtherRepair
from flask_login import login_required, current_user

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
                    flash(f"インポート中にエラーが発生しました: {result['error']}", 'danger')
                
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

def process_forklift_csv(df):
    """フォークリフトのCSVデータを処理"""
    try:
        count = 0
        for _, row in df.iterrows():
            # 必須フィールドの存在確認
            if 'asset_id' not in row or pd.isna(row['asset_id']):
                continue
                
            # 既存のフォークリフトを検索
            forklift = Forklift.query.filter_by(asset_id=row['asset_id']).first()
            
            # 新規作成または更新
            if forklift is None:
                forklift = Forklift()
                forklift.asset_id = row['asset_id']
            
            # 各フィールドを更新
            if 'name' in row and not pd.isna(row['name']):
                forklift.name = row['name']
            if 'model' in row and not pd.isna(row['model']):
                forklift.model = row['model']
            if 'manufacturer' in row and not pd.isna(row['manufacturer']):
                forklift.manufacturer = row['manufacturer']
            if 'forklift_type' in row and not pd.isna(row['forklift_type']):
                forklift.forklift_type = row['forklift_type']
            if 'power_source' in row and not pd.isna(row['power_source']):
                forklift.power_source = row['power_source']
            if 'max_load' in row and not pd.isna(row['max_load']):
                forklift.max_load = float(row['max_load'])
            if 'purchase_date' in row and not pd.isna(row['purchase_date']):
                forklift.purchase_date = pd.to_datetime(row['purchase_date']).date()
            if 'status' in row and not pd.isna(row['status']):
                forklift.status = row['status']
            if 'location' in row and not pd.isna(row['location']):
                forklift.location = row['location']
            if 'hour_meter' in row and not pd.isna(row['hour_meter']):
                forklift.hour_meter = float(row['hour_meter'])
            if 'ownership_type' in row and not pd.isna(row['ownership_type']):
                forklift.ownership_type = row['ownership_type']
            if 'notes' in row and not pd.isna(row['notes']):
                forklift.notes = row['notes']
            
            db.session.add(forklift)
            count += 1
        
        db.session.commit()
        return {'success': True, 'count': count}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def process_facility_csv(df):
    """倉庫施設のCSVデータを処理"""
    try:
        count = 0
        for _, row in df.iterrows():
            # 必須フィールドの存在確認
            if 'asset_id' not in row or pd.isna(row['asset_id']):
                continue
                
            # 既存の施設を検索
            facility = Facility.query.filter_by(asset_id=row['asset_id']).first()
            
            # 新規作成または更新
            if facility is None:
                facility = Facility()
                facility.asset_id = row['asset_id']
            
            # 各フィールドを更新
            if 'name' in row and not pd.isna(row['name']):
                facility.name = row['name']
            if 'location' in row and not pd.isna(row['location']):
                facility.location = row['location']
            if 'area' in row and not pd.isna(row['area']):
                facility.area = float(row['area'])
            if 'construction_date' in row and not pd.isna(row['construction_date']):
                facility.construction_date = pd.to_datetime(row['construction_date']).date()
            if 'status' in row and not pd.isna(row['status']):
                facility.status = row['status']
            if 'ownership_type' in row and not pd.isna(row['ownership_type']):
                facility.ownership_type = row['ownership_type']
            if 'notes' in row and not pd.isna(row['notes']):
                facility.notes = row['notes']
            
            db.session.add(facility)
            count += 1
        
        db.session.commit()
        return {'success': True, 'count': count}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def process_repair_csv(df):
    """修繕履歴のCSVデータを処理"""
    try:
        count = 0
        for _, row in df.iterrows():
            # 必須フィールドの存在確認
            if 'target_name' not in row or pd.isna(row['target_name']) or \
               'repair_date' not in row or pd.isna(row['repair_date']):
                continue
                
            # 新規修繕履歴を作成
            repair = OtherRepair()
            
            # 各フィールドを設定
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
        
        db.session.commit()
        return {'success': True, 'count': count}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}