from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from app.models import db
from app.models.forklift import Forklift, ForkliftPrediction
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from app.utils.file_utils import secure_filename_with_japanese
import uuid

annual_inspection_bp = Blueprint('annual_inspection', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}

@annual_inspection_bp.route('/forklift/<int:forklift_id>/annual-inspection', methods=['GET', 'POST'])
@login_required
def manage_annual_inspection(forklift_id):
    forklift = Forklift.query.get_or_404(forklift_id)
    prediction = ForkliftPrediction.query.filter_by(forklift_id=forklift_id).first()
    
    if not prediction:
        prediction = ForkliftPrediction(forklift_id=forklift_id)
        db.session.add(prediction)
        db.session.commit()
    
    if request.method == 'POST':
        inspection_date = request.form.get('inspection_date')
        inspection_status = request.form.get('inspection_status')
        inspection_notes = request.form.get('inspection_notes')
        operator = request.form.get('operator')
        
        if inspection_date:
            inspection_date = datetime.strptime(inspection_date, '%Y-%m-%d').date()
            prediction.annual_inspection_date = inspection_date
            # 次回点検日は1年後
            prediction.next_annual_inspection_date = inspection_date + timedelta(days=365)
        
        prediction.annual_inspection_status = inspection_status
        prediction.annual_inspection_notes = inspection_notes
        prediction.updated_by = operator
        
        # PDFファイルのアップロード処理
        if 'inspection_report' in request.files:
            file = request.files['inspection_report']
            if file and file.filename and allowed_file(file.filename):
                # 古いファイルがあれば削除
                if prediction.annual_inspection_report:
                    old_file_path = os.path.join(current_app.root_path, prediction.annual_inspection_report)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # オリジナルのファイル名を保持しつつ、一意性を確保するためのディレクトリ構造を使用
                filename = secure_filename_with_japanese(file.filename)
                
                # フォークリフトIDと日付を含むディレクトリを作成して一意性を確保
                date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_dir = os.path.join('annual_inspection', str(forklift_id), date_str)
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_dir)
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # ファイルを保存
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # 相対パスをDBに保存
                relative_path = os.path.join('static', 'uploads', unique_dir, filename)
                prediction.annual_inspection_report = relative_path
        
        db.session.commit()
        flash('年次点検情報が更新されました。', 'success')
        return redirect(url_for('forklift.view', id=forklift_id))
    
    return render_template('annual_inspection/manage.html', 
                          forklift=forklift, 
                          prediction=prediction)

@annual_inspection_bp.route('/annual-inspection/list')
@login_required
def list_annual_inspections():
    try:
        # 年次点検予定のフォークリフト一覧を取得
        # LEFT OUTER JOINを使用して、予測データがないフォークリフトも含める
        upcoming_inspections = db.session.query(
            Forklift, ForkliftPrediction
        ).outerjoin(
            ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
        ).filter(
            # アクティブなフォークリフトのみ表示
            Forklift.asset_status == 'active'
        ).order_by(
            # 次回点検日がある場合はその順、ない場合は管理番号順
            ForkliftPrediction.next_annual_inspection_date.asc().nullslast(),
            Forklift.management_number
        ).all()
        
        return render_template('annual_inspection/list.html', 
                              upcoming_inspections=upcoming_inspections)
    except Exception as e:
        # エラーログを記録
        current_app.logger.error(f"年次点検一覧取得エラー: {str(e)}")
        flash(f"年次点検一覧の取得中にエラーが発生しました: {str(e)}", "danger")
        return redirect(url_for('main.index'))

@annual_inspection_bp.route('/forklift/<int:forklift_id>/battery-tire', methods=['GET', 'POST'])
@login_required
def manage_battery_tire(forklift_id):
    """バッテリーとタイヤの交換時期を管理するルート"""
    forklift = Forklift.query.get_or_404(forklift_id)
    prediction = ForkliftPrediction.query.filter_by(forklift_id=forklift_id).first()
    
    if not prediction:
        prediction = ForkliftPrediction(forklift_id=forklift_id)
        db.session.add(prediction)
        db.session.commit()
    
    if request.method == 'POST':
        # バッテリー交換情報
        battery_replacement_date = request.form.get('battery_replacement_date')
        next_battery_replacement_date = request.form.get('next_battery_replacement_date')
        
        # タイヤ交換情報
        tire_replacement_date = request.form.get('tire_replacement_date')
        tire_type = request.form.get('tire_type')
        next_tire_replacement_date = request.form.get('next_tire_replacement_date')
        
        operator = request.form.get('operator_name', current_user.username)
        
        # 日付の変換
        if battery_replacement_date:
            prediction.battery_replacement_date = datetime.strptime(battery_replacement_date, '%Y-%m-%d').date()
        
        if next_battery_replacement_date:
            prediction.next_battery_replacement_date = datetime.strptime(next_battery_replacement_date, '%Y-%m-%d').date()
        
        if tire_replacement_date:
            prediction.tire_replacement_date = datetime.strptime(tire_replacement_date, '%Y-%m-%d').date()
        
        prediction.tire_type = tire_type
        
        if next_tire_replacement_date:
            prediction.next_tire_replacement_date = datetime.strptime(next_tire_replacement_date, '%Y-%m-%d').date()
        
        prediction.updated_by = operator
        db.session.commit()
        
        flash('バッテリー・タイヤ交換情報が更新されました。', 'success')
        return redirect(url_for('forklift.view', id=forklift_id))
    
    return render_template('annual_inspection/manage_battery_tire.html', 
                          forklift=forklift, 
                          prediction=prediction)

@annual_inspection_bp.route('/battery-tire/list')
@login_required
def list_battery_tire():
    """バッテリーとタイヤの交換予定一覧を表示するルート"""
    try:
        # 交換予定のフォークリフト一覧を取得
        # LEFT OUTER JOINを使用して、予測データがないフォークリフトも含める
        upcoming_replacements = db.session.query(
            Forklift, ForkliftPrediction
        ).outerjoin(
            ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
        ).filter(
            # アクティブなフォークリフトのみ表示
            Forklift.asset_status == 'active'
        ).all()
        
        # バッテリー交換予定日でソート
        battery_replacements = sorted(
            [item for item in upcoming_replacements if item[1] and item[1].next_battery_replacement_date],
            key=lambda x: x[1].next_battery_replacement_date
        )
        
        # タイヤ交換予定日でソート
        tire_replacements = sorted(
            [item for item in upcoming_replacements if item[1] and item[1].next_tire_replacement_date],
            key=lambda x: x[1].next_tire_replacement_date
        )
        
        return render_template('annual_inspection/battery_tire_list.html', 
                              battery_replacements=battery_replacements,
                              tire_replacements=tire_replacements)
    except Exception as e:
        # エラーログを記録
        current_app.logger.error(f"バッテリー・タイヤ交換一覧取得エラー: {str(e)}")
        flash(f"バッテリー・タイヤ交換一覧の取得中にエラーが発生しました: {str(e)}", "danger")
        return redirect(url_for('main.index'))