from app import create_app
from app.models import db
from app.models.forklift import Forklift, ForkliftRepair, ForkliftPrediction
from app.models.facility import Facility, FacilityRepair
from app.models.master import Employee, Contractor, WarehouseGroup, Manufacturer, Budget, EquipmentLifespan
from datetime import datetime, timedelta, date

def add_sample_data():
    app = create_app()
    with app.app_context():
        # マスターデータの追加
        add_master_data()
        
        # フォークリフトデータの追加
        add_forklift_data()
        
        # 倉庫施設データの追加
        add_facility_data()
        
        # 修繕履歴データの追加
        add_repair_data()
        
        # 予測データの追加
        add_prediction_data()
        
        print("サンプルデータを追加しました。")

def add_master_data():
    # 従業員データ
    employees = [
        Employee(name="田中太郎", department="物流部", position="マネージャー"),
        Employee(name="佐藤次郎", department="物流部", position="スーパーバイザー"),
        Employee(name="鈴木花子", department="管理部", position="経理担当"),
        Employee(name="高橋一郎", department="物流部", position="フォークリフトオペレーター"),
        Employee(name="伊藤健太", department="物流部", position="フォークリフトオペレーター")
    ]
    db.session.add_all(employees)
    
    # 業者データ
    contractors = [
        Contractor(name="株式会社フォークリフトサービス", contact_person="山田健二", phone="03-1234-5678", email="yamada@forklift-service.co.jp"),
        Contractor(name="建物メンテナンス株式会社", contact_person="佐々木直樹", phone="03-8765-4321", email="sasaki@building-maintenance.co.jp"),
        Contractor(name="タイヤ交換センター", contact_person="小林誠", phone="03-2345-6789", email="kobayashi@tire-center.co.jp"),
        Contractor(name="バッテリーショップ", contact_person="加藤裕子", phone="03-3456-7890", email="kato@battery-shop.co.jp"),
        Contractor(name="総合修理工場", contact_person="渡辺修", phone="03-4567-8901", email="watanabe@repair-factory.co.jp")
    ]
    db.session.add_all(contractors)
    
    # 倉庫グループデータ
    warehouse_groups = [
        WarehouseGroup(name="東京エリア", description="東京都内の倉庫グループ"),
        WarehouseGroup(name="神奈川エリア", description="神奈川県内の倉庫グループ"),
        WarehouseGroup(name="埼玉エリア", description="埼玉県内の倉庫グループ")
    ]
    db.session.add_all(warehouse_groups)
    
    # メーカーデータ
    manufacturers = [
        Manufacturer(name="トヨタ", country="日本", website="https://www.toyota-industries.co.jp/"),
        Manufacturer(name="ニチユ三菱", country="日本", website="https://www.nmf.co.jp/"),
        Manufacturer(name="コマツ", country="日本", website="https://home.komatsu/jp/"),
        Manufacturer(name="日立建機", country="日本", website="https://www.hitachicm.com/global/jp/")
    ]
    db.session.add_all(manufacturers)
    
    # 予算データ
    budgets = [
        Budget(year=2025, asset_type="forklift", amount=5000000),
        Budget(year=2025, asset_type="facility", amount=10000000),
        Budget(year=2025, asset_type="other", amount=2000000)
    ]
    db.session.add_all(budgets)
    
    # 設備耐用年数データ
    equipment_lifespans = [
        EquipmentLifespan(equipment_type="forklift", component="battery", expected_lifespan=36),  # 3年
        EquipmentLifespan(equipment_type="forklift", component="drive_tire", expected_lifespan=24),  # 2年
        EquipmentLifespan(equipment_type="forklift", component="caster_tire", expected_lifespan=18),  # 1.5年
        EquipmentLifespan(equipment_type="forklift", component="fork", expected_lifespan=60),  # 5年
        EquipmentLifespan(equipment_type="facility", component="air_conditioner", expected_lifespan=120),  # 10年
        EquipmentLifespan(equipment_type="facility", component="elevator", expected_lifespan=180)  # 15年
    ]
    db.session.add_all(equipment_lifespans)
    
    db.session.commit()

def add_forklift_data():
    # フォークリフトデータ
    forklifts = [
        Forklift(
            asset_management_number="FL-001",
            department="物流部",
            asset_type="forklift",
            acquisition_date=date(2020, 4, 1),
            useful_life=8,
            depreciation_rate=0.125,
            acquisition_cost=3500000,
            residual_value=1,
            asset_status="active",
            management_number="FL-R-001",
            manufacturer="トヨタ",
            forklift_type="reach",
            power_source="battery",
            model="7FBR15",
            serial_number="7FBR15-12345",
            load_capacity=1500,
            manufacture_date=date(2020, 3, 15),
            lift_height=4500,
            warehouse_group="東京エリア",
            warehouse_number="TK-01",
            floor="1F",
            operator="高橋一郎"
        ),
        Forklift(
            asset_management_number="FL-002",
            department="物流部",
            asset_type="forklift",
            acquisition_date=date(2018, 7, 1),
            useful_life=8,
            depreciation_rate=0.125,
            acquisition_cost=4200000,
            residual_value=1,
            asset_status="active",
            management_number="FL-C-001",
            manufacturer="ニチユ三菱",
            forklift_type="counter",
            power_source="diesel",
            model="FD25",
            serial_number="FD25-67890",
            load_capacity=2500,
            manufacture_date=date(2018, 6, 20),
            lift_height=3000,
            warehouse_group="東京エリア",
            warehouse_number="TK-01",
            floor="1F",
            operator="伊藤健太"
        ),
        Forklift(
            asset_management_number="FL-003",
            department="物流部",
            asset_type="forklift",
            acquisition_date=date(2021, 10, 1),
            useful_life=8,
            depreciation_rate=0.125,
            acquisition_cost=3800000,
            residual_value=1,
            asset_status="active",
            management_number="FL-R-002",
            manufacturer="トヨタ",
            forklift_type="reach",
            power_source="battery",
            model="7FBR15",
            serial_number="7FBR15-23456",
            load_capacity=1500,
            manufacture_date=date(2021, 9, 15),
            lift_height=4500,
            warehouse_group="神奈川エリア",
            warehouse_number="KN-01",
            floor="2F",
            operator="佐藤次郎"
        ),
        Forklift(
            asset_management_number="FL-004",
            department="物流部",
            asset_type="forklift",
            acquisition_date=date(2019, 5, 1),
            useful_life=8,
            depreciation_rate=0.125,
            acquisition_cost=4500000,
            residual_value=1,
            asset_status="under_repair",
            management_number="FL-C-002",
            manufacturer="コマツ",
            forklift_type="counter",
            power_source="lpg",
            model="FG25",
            serial_number="FG25-34567",
            load_capacity=2500,
            manufacture_date=date(2019, 4, 10),
            lift_height=3000,
            warehouse_group="神奈川エリア",
            warehouse_number="KN-01",
            floor="1F",
            operator="高橋一郎"
        ),
        Forklift(
            asset_management_number="FL-005",
            department="物流部",
            asset_type="forklift",
            acquisition_date=date(2022, 2, 1),
            useful_life=8,
            depreciation_rate=0.125,
            acquisition_cost=3600000,
            residual_value=1,
            asset_status="active",
            management_number="FL-R-003",
            manufacturer="ニチユ三菱",
            forklift_type="reach",
            power_source="battery",
            model="FBRF15",
            serial_number="FBRF15-45678",
            load_capacity=1500,
            manufacture_date=date(2022, 1, 20),
            lift_height=5000,
            warehouse_group="埼玉エリア",
            warehouse_number="ST-01",
            floor="1F",
            operator="伊藤健太"
        )
    ]
    db.session.add_all(forklifts)
    db.session.commit()

def add_facility_data():
    # 倉庫施設データ
    facilities = [
        Facility(
            asset_management_number="WH-001",
            department="物流部",
            asset_type="facility",
            acquisition_date=date(2010, 4, 1),
            useful_life=30,
            depreciation_rate=0.033,
            acquisition_cost=500000000,
            residual_value=1,
            asset_status="active",
            warehouse_number="TK-01",
            construction_date=date(2010, 3, 15),
            main_structure="鉄骨造",
            ownership_type="owned",
            floor_count=3
        ),
        Facility(
            asset_management_number="WH-002",
            department="物流部",
            asset_type="facility",
            acquisition_date=date(2015, 7, 1),
            useful_life=15,
            depreciation_rate=0.067,
            acquisition_cost=300000000,
            residual_value=1,
            asset_status="active",
            warehouse_number="KN-01",
            construction_date=date(2015, 6, 20),
            main_structure="鉄筋コンクリート造",
            ownership_type="leased",
            floor_count=2
        )
    ]
    db.session.add_all(facilities)
    db.session.commit()

def add_repair_data():
    # フォークリフト修繕履歴データ
    forklift_repairs = [
        ForkliftRepair(
            repair_date=date(2023, 5, 15),
            forklift_id=1,
            target_management_number="FL-R-001",
            contractor="株式会社フォークリフトサービス",
            repair_target_type="battery",
            repair_item="バッテリー交換",
            repair_cost=350000,
            repair_reason="wear",
            hour_meter=1500,
            notes="定期交換",
            operator="田中太郎"
        ),
        ForkliftRepair(
            repair_date=date(2024, 2, 10),
            forklift_id=1,
            target_management_number="FL-R-001",
            contractor="タイヤ交換センター",
            repair_target_type="drive_tire",
            repair_item="ドライブタイヤ交換",
            repair_cost=80000,
            repair_reason="wear",
            hour_meter=2300,
            notes="摩耗のため交換",
            operator="田中太郎"
        ),
        ForkliftRepair(
            repair_date=date(2023, 8, 20),
            forklift_id=2,
            target_management_number="FL-C-001",
            contractor="総合修理工場",
            repair_target_type="brake",
            repair_item="ブレーキ修理",
            repair_cost=120000,
            repair_reason="failure",
            hour_meter=3500,
            notes="ブレーキの効きが悪くなったため修理",
            operator="佐藤次郎"
        ),
        ForkliftRepair(
            repair_date=date(2024, 1, 5),
            forklift_id=2,
            target_management_number="FL-C-001",
            contractor="タイヤ交換センター",
            repair_target_type="caster_tire",
            repair_item="キャスタータイヤ交換",
            repair_cost=60000,
            repair_reason="wear",
            hour_meter=4200,
            notes="摩耗のため交換",
            operator="佐藤次郎"
        ),
        ForkliftRepair(
            repair_date=date(2023, 11, 12),
            forklift_id=3,
            target_management_number="FL-R-002",
            contractor="株式会社フォークリフトサービス",
            repair_target_type="fork",
            repair_item="フォーク修理",
            repair_cost=150000,
            repair_reason="accident",
            hour_meter=1200,
            notes="フォークが曲がったため修理",
            operator="田中太郎"
        ),
        ForkliftRepair(
            repair_date=date(2024, 3, 8),
            forklift_id=4,
            target_management_number="FL-C-002",
            contractor="総合修理工場",
            repair_target_type="motor",
            repair_item="エンジン修理",
            repair_cost=280000,
            repair_reason="failure",
            hour_meter=5100,
            notes="エンジンからの異音があったため修理",
            operator="佐藤次郎"
        ),
        ForkliftRepair(
            repair_date=date(2023, 9, 25),
            forklift_id=5,
            target_management_number="FL-R-003",
            contractor="バッテリーショップ",
            repair_target_type="electrical",
            repair_item="電気系統修理",
            repair_cost=90000,
            repair_reason="failure",
            hour_meter=800,
            notes="充電ができなくなったため修理",
            operator="田中太郎"
        )
    ]
    db.session.add_all(forklift_repairs)
    
    # 倉庫施設修繕履歴データ
    facility_repairs = [
        FacilityRepair(
            repair_date=date(2023, 6, 20),
            facility_id=1,
            target_warehouse_number="TK-01",
            floor="1F",
            contractor="建物メンテナンス株式会社",
            repair_item="床面補修",
            repair_cost=1500000,
            repair_reason="wear",
            notes="床面の摩耗が激しいため補修",
            operator="田中太郎"
        ),
        FacilityRepair(
            repair_date=date(2024, 1, 15),
            facility_id=1,
            target_warehouse_number="TK-01",
            floor="2F",
            contractor="建物メンテナンス株式会社",
            repair_item="空調設備修理",
            repair_cost=800000,
            repair_reason="failure",
            notes="空調設備の故障により修理",
            operator="佐藤次郎"
        ),
        FacilityRepair(
            repair_date=date(2023, 10, 5),
            facility_id=2,
            target_warehouse_number="KN-01",
            floor="1F",
            contractor="建物メンテナンス株式会社",
            repair_item="シャッター修理",
            repair_cost=450000,
            repair_reason="failure",
            notes="シャッターの開閉不良により修理",
            operator="田中太郎"
        )
    ]
    db.session.add_all(facility_repairs)
    db.session.commit()

def add_prediction_data():
    # フォークリフト予測データ
    predictions = [
        ForkliftPrediction(
            forklift_id=1,
            annual_inspection_date=date(2024, 3, 15),
            next_annual_inspection_date=date(2025, 3, 15),
            battery_replacement_date=date(2023, 5, 15),
            next_battery_replacement_date=date(2026, 5, 15),
            tire_replacement_date=date(2024, 2, 10),
            tire_type="drive",
            next_tire_replacement_date=date(2026, 2, 10)
        ),
        ForkliftPrediction(
            forklift_id=2,
            annual_inspection_date=date(2024, 6, 20),
            next_annual_inspection_date=date(2025, 6, 20),
            tire_replacement_date=date(2024, 1, 5),
            tire_type="caster",
            next_tire_replacement_date=date(2025, 7, 5)
        ),
        ForkliftPrediction(
            forklift_id=3,
            annual_inspection_date=date(2024, 9, 15),
            next_annual_inspection_date=date(2025, 9, 15)
        ),
        ForkliftPrediction(
            forklift_id=4,
            annual_inspection_date=date(2024, 4, 10),
            next_annual_inspection_date=date(2025, 4, 10)
        ),
        ForkliftPrediction(
            forklift_id=5,
            annual_inspection_date=date(2024, 1, 20),
            next_annual_inspection_date=date(2025, 1, 20)
        )
    ]
    db.session.add_all(predictions)
    db.session.commit()

if __name__ == '__main__':
    add_sample_data()