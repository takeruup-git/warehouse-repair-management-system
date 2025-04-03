from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Operator
from datetime import datetime

bp = Blueprint('operator', __name__)

@bp.route('/operators')
def index():
    operators = Operator.query.all()
    return render_template('operator/index.html', operators=operators)

@bp.route('/operators/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name']
        employee_id = request.form['employee_id']
        department = request.form['department']
        license_type = request.form['license_type']
        license_expiry = datetime.strptime(request.form['license_expiry'], '%Y-%m-%d').date() if request.form['license_expiry'] else None

        operator = Operator(
            name=name,
            employee_id=employee_id,
            department=department,
            license_type=license_type,
            license_expiry=license_expiry
        )

        try:
            db.session.add(operator)
            db.session.commit()
            flash('操作者を登録しました。', 'success')
            return redirect(url_for('operator.index'))
        except Exception as e:
            db.session.rollback()
            flash('操作者の登録に失敗しました。', 'error')
            return render_template('operator/create.html')

    return render_template('operator/create.html')

@bp.route('/operators/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    operator = Operator.query.get_or_404(id)

    if request.method == 'POST':
        operator.name = request.form['name']
        operator.employee_id = request.form['employee_id']
        operator.department = request.form['department']
        operator.license_type = request.form['license_type']
        operator.license_expiry = datetime.strptime(request.form['license_expiry'], '%Y-%m-%d').date() if request.form['license_expiry'] else None

        try:
            db.session.commit()
            flash('操作者情報を更新しました。', 'success')
            return redirect(url_for('operator.index'))
        except Exception as e:
            db.session.rollback()
            flash('操作者情報の更新に失敗しました。', 'error')

    return render_template('operator/edit.html', operator=operator)

@bp.route('/operators/<int:id>/delete', methods=['POST'])
def delete(id):
    operator = Operator.query.get_or_404(id)
    try:
        db.session.delete(operator)
        db.session.commit()
        flash('操作者を削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作者の削除に失敗しました。', 'error')
    
    return redirect(url_for('operator.index'))