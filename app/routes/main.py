from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import db
from app.models.forklift import Forklift, ForkliftRepair, ForkliftPrediction
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from config import Config
from flask_login import login_required
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    # ダッシュボード用のデータを取得
    
    # 1. 月別修繕費推移データ
    current_year = Config.CURRENT_DATE.year
    
    # フォークリフト修繕費
    monthly_costs_query = db.session.query(
        extract('month', ForkliftRepair.repair_date).label('month'),
        func.sum(ForkliftRepair.repair_cost).label('cost')
    ).filter(
        extract('year', ForkliftRepair.repair_date) == current_year
    ).group_by(
        extract('month', ForkliftRepair.repair_date)
    )
    
    # SQLを出力してデバッグ
    print("フォークリフト修繕費クエリ:", str(monthly_costs_query))
    monthly_costs = monthly_costs_query.all()
    print("フォークリフト修繕費結果:", monthly_costs)
    
    # 倉庫施設修繕費
    monthly_costs_facility_query = db.session.query(
        extract('month', FacilityRepair.repair_date).label('month'),
        func.sum(FacilityRepair.repair_cost).label('cost')
    ).filter(
        extract('year', FacilityRepair.repair_date) == current_year
    ).group_by(
        extract('month', FacilityRepair.repair_date)
    )
    
    print("倉庫施設修繕費クエリ:", str(monthly_costs_facility_query))
    monthly_costs_facility = monthly_costs_facility_query.all()
    print("倉庫施設修繕費結果:", monthly_costs_facility)
    
    # その他修繕費
    monthly_costs_other_query = db.session.query(
        extract('month', OtherRepair.repair_date).label('month'),
        func.sum(OtherRepair.repair_cost).label('cost')
    ).filter(
        extract('year', OtherRepair.repair_date) == current_year
    ).group_by(
        extract('month', OtherRepair.repair_date)
    )
    
    print("その他修繕費クエリ:", str(monthly_costs_other_query))
    monthly_costs_other = monthly_costs_other_query.all()
    print("その他修繕費結果:", monthly_costs_other)
    
    # 月別データを整形
    months = list(range(1, 13))
    forklift_costs = [0] * 12
    facility_costs = [0] * 12
    other_costs = [0] * 12
    
    # 結果がNoneの場合に対応
    if monthly_costs:
        for month, cost in monthly_costs:
            forklift_costs[int(month) - 1] = int(cost or 0)
    
    if monthly_costs_facility:
        for month, cost in monthly_costs_facility:
            facility_costs[int(month) - 1] = int(cost or 0)
    
    if monthly_costs_other:
        for month, cost in monthly_costs_other:
            other_costs[int(month) - 1] = int(cost or 0)
    
    # 2. 修繕費上位5号車
    top_vehicles = db.session.query(
        ForkliftRepair.target_management_number,
        func.sum(ForkliftRepair.repair_cost).label('total_cost')
    ).group_by(
        ForkliftRepair.target_management_number
    ).order_by(
        func.sum(ForkliftRepair.repair_cost).desc()
    ).limit(5).all()
    
    # 3. 1年以内の交換・点検アラート
    one_year_later = Config.CURRENT_DATE + timedelta(days=365)
    alerts = []
    
    # バッテリー交換アラート
    battery_alerts_query = db.session.query(
        Forklift.management_number,
        ForkliftPrediction.next_battery_replacement_date
    ).join(
        ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
    ).filter(
        ForkliftPrediction.next_battery_replacement_date <= one_year_later,
        ForkliftPrediction.next_battery_replacement_date >= Config.CURRENT_DATE,
        Forklift.asset_status == 'active'  # アクティブなフォークリフトのみ
    )
    
    # SQLクエリをログに出力
    current_app.logger.info(f"バッテリー交換アラートクエリ: {str(battery_alerts_query)}")
    
    battery_alerts = battery_alerts_query.all()
    
    # 結果をログに出力
    current_app.logger.info(f"バッテリー交換アラート結果: {len(battery_alerts)}件")
    
    for management_number, replacement_date in battery_alerts:
        alerts.append({
            'management_number': management_number,
            'item': 'バッテリー交換',
            'date': replacement_date.strftime('%Y-%m-%d'),
            'days_left': (replacement_date - Config.CURRENT_DATE.date()).days
        })
    
    # タイヤ交換アラート
    tire_alerts_query = db.session.query(
        Forklift.management_number,
        ForkliftPrediction.next_tire_replacement_date,
        ForkliftPrediction.tire_type
    ).join(
        ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
    ).filter(
        ForkliftPrediction.next_tire_replacement_date <= one_year_later,
        ForkliftPrediction.next_tire_replacement_date >= Config.CURRENT_DATE,
        Forklift.asset_status == 'active'  # アクティブなフォークリフトのみ
    )
    
    # SQLクエリをログに出力
    current_app.logger.info(f"タイヤ交換アラートクエリ: {str(tire_alerts_query)}")
    
    tire_alerts = tire_alerts_query.all()
    
    # 結果をログに出力
    current_app.logger.info(f"タイヤ交換アラート結果: {len(tire_alerts)}件")
    
    for management_number, replacement_date, tire_type in tire_alerts:
        tire_type_name = "ドライブタイヤ" if tire_type == "drive" else "キャスタータイヤ"
        alerts.append({
            'management_number': management_number,
            'item': f'{tire_type_name}交換',
            'date': replacement_date.strftime('%Y-%m-%d'),
            'days_left': (replacement_date - Config.CURRENT_DATE.date()).days
        })
    
    # 年次点検アラート
    inspection_alerts_query = db.session.query(
        Forklift.management_number,
        ForkliftPrediction.next_annual_inspection_date
    ).join(
        ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
    ).filter(
        ForkliftPrediction.next_annual_inspection_date <= one_year_later,
        ForkliftPrediction.next_annual_inspection_date >= Config.CURRENT_DATE,
        Forklift.asset_status == 'active'  # アクティブなフォークリフトのみ
    )
    
    # SQLクエリをログに出力
    current_app.logger.info(f"年次点検アラートクエリ: {str(inspection_alerts_query)}")
    
    inspection_alerts = inspection_alerts_query.all()
    
    # 結果をログに出力
    current_app.logger.info(f"年次点検アラート結果: {len(inspection_alerts)}件")
    
    for management_number, inspection_date in inspection_alerts:
        alerts.append({
            'management_number': management_number,
            'item': '年次点検',
            'date': inspection_date.strftime('%Y-%m-%d'),
            'days_left': (inspection_date - Config.CURRENT_DATE.date()).days
        })
    
    # 日数でソート
    alerts.sort(key=lambda x: x['days_left'])
    
    # 4. 最近の修繕履歴
    recent_repairs = db.session.query(ForkliftRepair).order_by(ForkliftRepair.repair_date.desc()).limit(5).all()
    recent_facility_repairs = db.session.query(FacilityRepair).order_by(FacilityRepair.repair_date.desc()).limit(5).all()
    
    # 5. PDFファイル数を取得
    pdf_count = 0
    pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf')
    if os.path.exists(pdf_dir):
        pdf_count = len([f for f in os.listdir(pdf_dir) if f.endswith('.pdf')])
    
    return render_template('index.html',
                          months=months,
                          forklift_costs=forklift_costs,
                          facility_costs=facility_costs,
                          other_costs=other_costs,
                          top_vehicles=top_vehicles,
                          alerts=alerts,
                          recent_repairs=recent_repairs,
                          recent_facility_repairs=recent_facility_repairs,
                          pdf_count=pdf_count)

@main_bp.route('/about')
@login_required
def about():
    return render_template('about.html')