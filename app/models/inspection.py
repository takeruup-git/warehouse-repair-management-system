from app.models import db
from datetime import datetime
from config import Config

class BatteryFluidCheck(db.Model):
    __tablename__ = 'battery_fluid_checks'
    
    id = db.Column(db.Integer, primary_key=True)
    check_date = db.Column(db.Date, nullable=False, index=True)
    forklift_id = db.Column(db.Integer, db.ForeignKey('forklifts.id'), nullable=False)
    management_number = db.Column(db.String(50), nullable=False)
    warehouse = db.Column(db.String(50), nullable=False)
    elapsed_years = db.Column(db.Float, nullable=False)
    fluid_level = db.Column(db.String(20), nullable=False)  # OK, Low, etc.
    refill_date = db.Column(db.Date)
    refiller = db.Column(db.String(100))
    confirmation_date = db.Column(db.Date, nullable=False)
    inspector = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    operator = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    forklift = db.relationship('Forklift')
    
    def __repr__(self):
        return f'<BatteryFluidCheck {self.id} for {self.management_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'check_date': self.check_date.strftime('%Y-%m-%d') if self.check_date else None,
            'forklift_id': self.forklift_id,
            'management_number': self.management_number,
            'warehouse': self.warehouse,
            'elapsed_years': self.elapsed_years,
            'fluid_level': self.fluid_level,
            'refill_date': self.refill_date.strftime('%Y-%m-%d') if self.refill_date else None,
            'refiller': self.refiller,
            'confirmation_date': self.confirmation_date.strftime('%Y-%m-%d') if self.confirmation_date else None,
            'inspector': self.inspector,
            'notes': self.notes,
            'operator': self.operator
        }

class PeriodicSelfInspection(db.Model):
    __tablename__ = 'periodic_self_inspections'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_date = db.Column(db.Date, nullable=False, index=True)
    forklift_id = db.Column(db.Integer, db.ForeignKey('forklifts.id'), nullable=False)
    management_number = db.Column(db.String(50), nullable=False)
    inspection_type = db.Column(db.String(20), nullable=False)  # engine, battery_reach, battery_counter
    motor_condition = db.Column(db.String(10))  # good, bad
    tire_condition = db.Column(db.String(10))  # good, bad
    fork_condition = db.Column(db.String(10))  # good, bad
    repair_action = db.Column(db.String(10))  # X, △, A, T, C, L, -
    inspector = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    operator = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    forklift = db.relationship('Forklift')
    
    @property
    def motor_condition_name(self):
        return Config.INSPECTION_RESULT_NAMES.get(self.motor_condition, self.motor_condition)
    
    @property
    def tire_condition_name(self):
        return Config.INSPECTION_RESULT_NAMES.get(self.tire_condition, self.tire_condition)
    
    @property
    def fork_condition_name(self):
        return Config.INSPECTION_RESULT_NAMES.get(self.fork_condition, self.fork_condition)
    
    @property
    def repair_action_name(self):
        return Config.REPAIR_ACTION_NAMES.get(self.repair_action, self.repair_action)
    
    def __repr__(self):
        return f'<PeriodicSelfInspection {self.id} for {self.management_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'inspection_date': self.inspection_date.strftime('%Y-%m-%d') if self.inspection_date else None,
            'forklift_id': self.forklift_id,
            'management_number': self.management_number,
            'inspection_type': self.inspection_type,
            'motor_condition': self.motor_condition,
            'motor_condition_name': self.motor_condition_name,
            'tire_condition': self.tire_condition,
            'tire_condition_name': self.tire_condition_name,
            'fork_condition': self.fork_condition,
            'fork_condition_name': self.fork_condition_name,
            'repair_action': self.repair_action,
            'repair_action_name': self.repair_action_name,
            'inspector': self.inspector,
            'notes': self.notes,
            'operator': self.operator
        }

class PreShiftInspection(db.Model):
    __tablename__ = 'pre_shift_inspections'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_date = db.Column(db.Date, nullable=False, index=True)
    forklift_id = db.Column(db.Integer, db.ForeignKey('forklifts.id'), nullable=False)
    management_number = db.Column(db.String(50), nullable=False)
    inspection_type = db.Column(db.String(20), nullable=False)  # engine, battery
    hour_meter = db.Column(db.Integer, nullable=False)
    operating_hours = db.Column(db.Float, nullable=False)
    fluid_refill = db.Column(db.Float)  # リットル
    engine_oil = db.Column(db.String(10))  # engine only
    brake_condition = db.Column(db.String(10))  # engine only
    battery_fluid = db.Column(db.String(10))  # battery only
    tire_pressure = db.Column(db.String(10))  # battery only
    inspector = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    operator = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    forklift = db.relationship('Forklift')
    
    def __repr__(self):
        return f'<PreShiftInspection {self.id} for {self.management_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'inspection_date': self.inspection_date.strftime('%Y-%m-%d') if self.inspection_date else None,
            'forklift_id': self.forklift_id,
            'management_number': self.management_number,
            'inspection_type': self.inspection_type,
            'hour_meter': self.hour_meter,
            'operating_hours': self.operating_hours,
            'fluid_refill': self.fluid_refill,
            'engine_oil': self.engine_oil,
            'brake_condition': self.brake_condition,
            'battery_fluid': self.battery_fluid,
            'tire_pressure': self.tire_pressure,
            'inspector': self.inspector,
            'notes': self.notes,
            'operator': self.operator
        }