from app import create_app
from app.models import db
from app.models.master import Employee, Contractor, WarehouseGroup, Manufacturer, Budget, EquipmentLifespan

def init_db():
    app = create_app()
    with app.app_context():
        # データベースを初期化
        db.drop_all()
        db.create_all()
        
        print("データベースを初期化しました。")

if __name__ == '__main__':
    init_db()
