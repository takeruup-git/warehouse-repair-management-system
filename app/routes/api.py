from flask import Blueprint, jsonify, request
from app.models import db
from app.models.forklift import Forklift, ForkliftRepair, ForkliftPrediction
from app.models.facility import Facility, FacilityRepair
from app.models.other_repair import OtherRepair
from app.models.master import Employee, Contractor, WarehouseGroup, Manufacturer, Budget, EquipmentLifespan
from app.models.inspection import BatteryFluidCheck, PeriodicSelfInspection, PreShiftInspection
from app.models.file import FileMetadata
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from config import Config

api_bp = Blueprint('api', __name__)

@api_bp.route('/forklifts')
def get_forklifts():
    forklifts = Forklift.query.all()
    return jsonify([forklift.to_dict() for forklift in forklifts])

@api_bp.route('/forklifts/<int:id>')
def get_forklift(id):
    forklift = Forklift.query.get_or_404(id)
    return jsonify(forklift.to_dict())

@api_bp.route('/forklifts/<int:id>/repairs')
def get_forklift_repairs(id):
    repairs = ForkliftRepair.query.filter_by(forklift_id=id).order_by(ForkliftRepair.repair_date.desc()).all()
    return jsonify([repair.to_dict() for repair in repairs])

@api_bp.route('/facilities')
def get_facilities():
    facilities = Facility.query.all()
    return jsonify([facility.to_dict() for facility in facilities])

@api_bp.route('/facilities/<int:id>')
def get_facility(id):
    facility = Facility.query.get_or_404(id)
    return jsonify(facility.to_dict())

@api_bp.route('/facilities/<int:id>/repairs')
def get_facility_repairs(id):
    repairs = FacilityRepair.query.filter_by(facility_id=id).order_by(FacilityRepair.repair_date.desc()).all()
    return jsonify([repair.to_dict() for repair in repairs])

@api_bp.route('/other_repairs')
def get_other_repairs():
    repairs = OtherRepair.query.order_by(OtherRepair.repair_date.desc()).all()
    return jsonify([repair.to_dict() for repair in repairs])

@api_bp.route('/file_metadata')
def get_file_metadata():
    file_path = request.args.get('file_path')
    if not file_path:
        return jsonify({'success': False, 'error': 'File path is required'})
    
    metadata = FileMetadata.query.filter_by(file_path=file_path).first()
    if metadata:
        return jsonify({
            'success': True,
            'metadata': metadata.to_dict()
        })
    else:
        return jsonify({'success': False, 'error': 'File metadata not found'})

@api_bp.route('/files')
def get_files():
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')
    
    if not entity_type or not entity_id:
        return jsonify({'success': False, 'error': 'Entity type and ID are required'})
    
    try:
        entity_id = int(entity_id)
        files = FileMetadata.query.filter_by(entity_type=entity_type, entity_id=entity_id).order_by(FileMetadata.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'files': [file.to_dict() for file in files]
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/dashboard/monthly_costs')
def get_monthly_costs():
    current_year = Config.CURRENT_DATE.year
    
    # フォークリフト修繕費
    forklift_costs = db.session.query(
        extract('month', ForkliftRepair.repair_date).label('month'),
        func.sum(ForkliftRepair.repair_cost).label('cost')
    ).filter(
        extract('year', ForkliftRepair.repair_date) == current_year
    ).group_by(
        extract('month', ForkliftRepair.repair_date)
    ).all()
    
    # 倉庫施設修繕費
    facility_costs = db.session.query(
        extract('month', FacilityRepair.repair_date).label('month'),
        func.sum(FacilityRepair.repair_cost).label('cost')
    ).filter(
        extract('year', FacilityRepair.repair_date) == current_year
    ).group_by(
        extract('month', FacilityRepair.repair_date)
    ).all()
    
    # その他修繕費
    other_costs = db.session.query(
        extract('month', OtherRepair.repair_date).label('month'),
        func.sum(OtherRepair.repair_cost).label('cost')
    ).filter(
        extract('year', OtherRepair.repair_date) == current_year
    ).group_by(
        extract('month', OtherRepair.repair_date)
    ).all()
    
    # 月別データを整形
    months = list(range(1, 13))
    forklift_data = [0] * 12
    facility_data = [0] * 12
    other_data = [0] * 12
    
    for month, cost in forklift_costs:
        forklift_data[int(month) - 1] = int(cost or 0)
    
    for month, cost in facility_costs:
        facility_data[int(month) - 1] = int(cost or 0)
    
    for month, cost in other_costs:
        other_data[int(month) - 1] = int(cost or 0)
    
    return jsonify({
        'months': months,
        'forklift_costs': forklift_data,
        'facility_costs': facility_data,
        'other_costs': other_data
    })

@api_bp.route('/dashboard/top_vehicles')
def get_top_vehicles():
    # 修繕費上位5号車
    top_vehicles = db.session.query(
        ForkliftRepair.target_management_number,
        func.sum(ForkliftRepair.repair_cost).label('total_cost')
    ).group_by(
        ForkliftRepair.target_management_number
    ).order_by(
        func.sum(ForkliftRepair.repair_cost).desc()
    ).limit(5).all()
    
    result = []
    for management_number, total_cost in top_vehicles:
        result.append({
            'management_number': management_number,
            'total_cost': int(total_cost)
        })
    
    return jsonify(result)

@api_bp.route('/dashboard/alerts')
def get_alerts():
    one_year_later = Config.CURRENT_DATE + timedelta(days=365)
    alerts = []
    
    # バッテリー交換アラート
    battery_alerts = db.session.query(
        Forklift.management_number,
        ForkliftPrediction.next_battery_replacement_date
    ).join(
        ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
    ).filter(
        ForkliftPrediction.next_battery_replacement_date <= one_year_later,
        ForkliftPrediction.next_battery_replacement_date >= Config.CURRENT_DATE
    ).all()
    
    for management_number, replacement_date in battery_alerts:
        alerts.append({
            'management_number': management_number,
            'item': 'バッテリー交換',
            'date': replacement_date.strftime('%Y-%m-%d'),
            'days_left': (replacement_date - Config.CURRENT_DATE.date()).days
        })
    
    # タイヤ交換アラート
    tire_alerts = db.session.query(
        Forklift.management_number,
        ForkliftPrediction.next_tire_replacement_date,
        ForkliftPrediction.tire_type
    ).join(
        ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
    ).filter(
        ForkliftPrediction.next_tire_replacement_date <= one_year_later,
        ForkliftPrediction.next_tire_replacement_date >= Config.CURRENT_DATE
    ).all()
    
    for management_number, replacement_date, tire_type in tire_alerts:
        tire_type_name = "ドライブタイヤ" if tire_type == "drive" else "キャスタータイヤ"
        alerts.append({
            'management_number': management_number,
            'item': f'{tire_type_name}交換',
            'date': replacement_date.strftime('%Y-%m-%d'),
            'days_left': (replacement_date - Config.CURRENT_DATE.date()).days
        })
    
    # 年次点検アラート
    inspection_alerts = db.session.query(
        Forklift.management_number,
        ForkliftPrediction.next_annual_inspection_date
    ).join(
        ForkliftPrediction, Forklift.id == ForkliftPrediction.forklift_id
    ).filter(
        ForkliftPrediction.next_annual_inspection_date <= one_year_later,
        ForkliftPrediction.next_annual_inspection_date >= Config.CURRENT_DATE
    ).all()
    
    for management_number, inspection_date in inspection_alerts:
        alerts.append({
            'management_number': management_number,
            'item': '年次点検',
            'date': inspection_date.strftime('%Y-%m-%d'),
            'days_left': (inspection_date - Config.CURRENT_DATE.date()).days
        })
    
    # 日数でソート
    alerts.sort(key=lambda x: x['days_left'])
    
    return jsonify(alerts)

@api_bp.route('/masters/employees')
def get_employees():
    employees = Employee.query.filter_by(is_active=True).all()
    return jsonify([employee.to_dict() for employee in employees])

@api_bp.route('/masters/contractors')
def get_contractors():
    contractors = Contractor.query.filter_by(is_active=True).all()
    return jsonify([contractor.to_dict() for contractor in contractors])

@api_bp.route('/masters/warehouse_groups')
def get_warehouse_groups():
    warehouse_groups = WarehouseGroup.query.filter_by(is_active=True).all()
    return jsonify([group.to_dict() for group in warehouse_groups])

@api_bp.route('/masters/manufacturers')
def get_manufacturers():
    manufacturers = Manufacturer.query.filter_by(is_active=True).all()
    return jsonify([manufacturer.to_dict() for manufacturer in manufacturers])

@api_bp.route('/masters/budgets')
def get_budgets():
    year = request.args.get('year', Config.CURRENT_DATE.year, type=int)
    budgets = Budget.query.filter_by(year=year).all()
    return jsonify([budget.to_dict() for budget in budgets])

@api_bp.route('/masters/equipment_lifespans')
def get_equipment_lifespans():
    equipment_type = request.args.get('equipment_type')
    
    query = EquipmentLifespan.query
    if equipment_type:
        query = query.filter_by(equipment_type=equipment_type)
    
    lifespans = query.all()
    return jsonify([lifespan.to_dict() for lifespan in lifespans])