# ルートパッケージ初期化
from flask import Blueprint

from . import main, facility, forklift, repair, report, inspection, operator

def init_app(app):
    app.register_blueprint(main.bp)
    app.register_blueprint(facility.bp)
    app.register_blueprint(forklift.bp)
    app.register_blueprint(repair.bp)
    app.register_blueprint(report.bp)
    app.register_blueprint(inspection.bp)
    app.register_blueprint(operator.bp)