from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.models import db
from app.models.operator import Operator
from datetime import datetime
from flask_login import login_required

operator_bp = Blueprint('operator', __name__)

@operator_bp.route('/')
@login_required
def index():
    """操作者一覧を表示"""
    operators = Operator.query.order_by(Operator.name).all()
    return render_template('operator/index.html', operators=operators)

@operator_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """新規操作者を作成"""
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        department = request.form.get('department')
        license_number = request.form.get('license_number')
        license_expiry = request.form.get('license_expiry')
        
        if not employee_id or not name:
            flash('社員IDと名前は必須です', 'danger')
            return redirect(url_for('operator.create'))
        
        # 既存の社員IDをチェック
        existing_operator = Operator.query.filter_by(employee_id=employee_id).first()
        if existing_operator:
            flash('この社員IDは既に登録されています', 'danger')
            return redirect(url_for('operator.create'))
        
        # 日付変換
        license_expiry_date = None
        if license_expiry:
            try:
                license_expiry_date = datetime.strptime(license_expiry, '%Y-%m-%d').date()
            except ValueError:
                flash('免許期限の日付形式が正しくありません', 'danger')
                return redirect(url_for('operator.create'))
        
        # 新規操作者を作成
        operator = Operator(
            employee_id=employee_id,
            name=name,
            department=department,
            license_number=license_number,
            license_expiry=license_expiry_date,
            updated_by=request.form.get('operator_name', 'システム')
        )
        
        db.session.add(operator)
        db.session.commit()
        
        flash('操作者を登録しました', 'success')
        return redirect(url_for('operator.index'))
    
    return render_template('operator/create.html')

@operator_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """操作者情報を編集"""
    operator = Operator.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        department = request.form.get('department')
        license_number = request.form.get('license_number')
        license_expiry = request.form.get('license_expiry')
        status = request.form.get('status')
        
        if not name:
            flash('名前は必須です', 'danger')
            return redirect(url_for('operator.edit', id=id))
        
        # 日付変換
        license_expiry_date = None
        if license_expiry:
            try:
                license_expiry_date = datetime.strptime(license_expiry, '%Y-%m-%d').date()
            except ValueError:
                flash('免許期限の日付形式が正しくありません', 'danger')
                return redirect(url_for('operator.edit', id=id))
        
        # 操作者情報を更新
        operator.name = name
        operator.department = department
        operator.license_number = license_number
        operator.license_expiry = license_expiry_date
        if status:
            operator.status = status
        operator.updated_by = request.form.get('operator_name', 'システム')
        operator.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('操作者情報を更新しました', 'success')
        return redirect(url_for('operator.index'))
    
    return render_template('operator/edit.html', operator=operator)

@operator_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """操作者を削除"""
    operator = Operator.query.get_or_404(id)
    
    db.session.delete(operator)
    db.session.commit()
    
    flash('操作者を削除しました', 'success')
    return redirect(url_for('operator.index'))

@operator_bp.route('/api/list')
def api_list():
    """操作者一覧をJSON形式で返す（モーダル用）"""
    operators = Operator.query.filter_by(status='active').order_by(Operator.name).all()
    return jsonify([{'id': op.id, 'name': op.name, 'employee_id': op.employee_id} for op in operators])

@operator_bp.route('/api/set_current', methods=['POST'])
def api_set_current():
    """現在の操作者をセッションに設定"""
    data = request.get_json()
    operator_id = data.get('operator_id')
    operator_name = data.get('operator_name')
    
    if operator_id:
        operator = Operator.query.get(operator_id)
        if operator:
            session['current_operator_id'] = operator.id
            session['current_operator_name'] = operator.name
            
            # 最終使用日時を更新
            operator.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'success': True, 'name': operator.name})
    elif operator_name:
        # 新規操作者名の場合は登録
        existing = Operator.query.filter_by(name=operator_name).first()
        if existing:
            session['current_operator_id'] = existing.id
            session['current_operator_name'] = existing.name
            
            # 最終使用日時を更新
            existing.updated_at = datetime.utcnow()
            db.session.commit()
        else:
            # 新規作成（簡易登録）
            new_operator = Operator(
                employee_id=f"TEMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                name=operator_name,
                updated_by='システム（自動登録）'
            )
            db.session.add(new_operator)
            db.session.commit()
            
            session['current_operator_id'] = new_operator.id
            session['current_operator_name'] = new_operator.name
        
        return jsonify({'success': True, 'name': operator_name})
    
    return jsonify({'success': False, 'error': '操作者情報が不正です'}), 400

@operator_bp.route('/api/get_current')
def api_get_current():
    """現在の操作者をJSON形式で返す"""
    operator_id = session.get('current_operator_id')
    operator_name = session.get('current_operator_name')
    
    if operator_id and operator_name:
        return jsonify({
            'success': True,
            'operator_id': operator_id,
            'operator_name': operator_name
        })
    
    return jsonify({'success': False})