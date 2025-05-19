from app.models import db
from datetime import datetime

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Employee {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'department': self.department,
            'position': self.position,
            'is_active': self.is_active
        }

class MasterItem(db.Model):
    __tablename__ = 'master_items'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # forklift_type, power_source, warehouse_group, etc.
    key = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('category', 'key', name='uix_category_key'),
    )
    
    def __repr__(self):
        return f'<MasterItem {self.category}:{self.key}={self.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }

class Contractor(db.Model):
    __tablename__ = 'contractors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contractor {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'is_active': self.is_active
        }

class WarehouseGroup(db.Model):
    __tablename__ = 'warehouse_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WarehouseGroup {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active
        }

class Manufacturer(db.Model):
    __tablename__ = 'manufacturers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50))
    website = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Manufacturer {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'country': self.country,
            'website': self.website,
            'is_active': self.is_active
        }

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    asset_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Budget {self.year} for {self.asset_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'asset_type': self.asset_type,
            'amount': self.amount
        }

class EquipmentLifespan(db.Model):
    __tablename__ = 'equipment_lifespans'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_type = db.Column(db.String(50), nullable=False)
    component = db.Column(db.String(50), nullable=False)
    expected_lifespan = db.Column(db.Integer, nullable=False)  # 月数
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EquipmentLifespan {self.equipment_type} {self.component}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'equipment_type': self.equipment_type,
            'component': self.component,
            'expected_lifespan': self.expected_lifespan
        }