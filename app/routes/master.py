from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, AuditLog
from app.models.master import MasterItem
from flask_login import login_required
from config import Config
from sqlalchemy import func

master_bp = Blueprint('master', __name__)

@master_bp.route('/')
@login_required
def index():
    """マスターデータ管理のメインページ"""
    # カテゴリ一覧を取得
    categories = db.session.query(MasterItem.category, func.count(MasterItem.id)).group_by(MasterItem.category).all()
    
    # 設定ファイルからカテゴリ名を取得
    category_names = {
        'forklift_type': 'フォークリフトタイプ',
        'power_source': '動力源',
        'warehouse_group': '倉庫グループ',
        'repair_target_type': '修繕対象種別',
        'repair_reason': '修繕理由',
        'asset_status': '資産ステータス',
        'ownership_type': '所有形態',
        'department': '部門',
        'manufacturer': 'メーカー',
        'warehouse_number': '倉庫番号',
        'floor': '階層',
        'operator': '取扱担当者',
        'department': '部門',
        'manufacturer': 'メーカー',
        'warehouse_number': '倉庫番号',
        'floor': '階層',
        'operator': '取扱担当者'
    }
    
    # カテゴリ情報を整形
    category_info = []
    for category, count in categories:
        category_info.append({
            'id': category,
            'name': category_names.get(category, category),
            'count': count
        })
    
    return render_template('master/index.html', categories=category_info)

@master_bp.route('/category/<category>')
@login_required
def category(category):
    """特定のカテゴリのマスターデータ一覧を表示"""
    items = MasterItem.query.filter_by(category=category).order_by(MasterItem.sort_order, MasterItem.key).all()
    
    # カテゴリ名を取得
    category_names = {
        'forklift_type': 'フォークリフトタイプ',
        'power_source': '動力源',
        'warehouse_group': '倉庫グループ',
        'repair_target_type': '修繕対象種別',
        'repair_reason': '修繕理由',
        'asset_status': '資産ステータス',
        'ownership_type': '所有形態',
        'department': '部門',
        'manufacturer': 'メーカー',
        'warehouse_number': '倉庫番号',
        'floor': '階層',
        'operator': '取扱担当者'
    }
    category_name = category_names.get(category, category)
    
    return render_template('master/category.html', 
                          category=category, 
                          category_name=category_name, 
                          items=items)

@master_bp.route('/create/<category>', methods=['GET', 'POST'])
@login_required
def create(category):
    """マスターデータの新規作成"""
    if request.method == 'POST':
        key = request.form.get('key')
        value = request.form.get('value')
        description = request.form.get('description')
        sort_order = request.form.get('sort_order', 0)
        
        # 必須項目の検証
        if not key or not value:
            flash('キーと値は必須項目です', 'danger')
            return redirect(request.url)
        
        # 既存のキーがないか確認
        existing = MasterItem.query.filter_by(category=category, key=key).first()
        if existing:
            flash('このキーは既に使用されています', 'danger')
            return redirect(request.url)
        
        try:
            # 新しいマスターアイテムを作成
            item = MasterItem(
                category=category,
                key=key,
                value=value,
                description=description,
                sort_order=int(sort_order) if sort_order else 0
            )
            
            db.session.add(item)
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='master_item',
                entity_id=item.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'マスターデータ {category}:{key} を作成'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('マスターデータが正常に作成されました', 'success')
            return redirect(url_for('master.category', category=category))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # カテゴリ名を取得
    category_names = {
        'forklift_type': 'フォークリフトタイプ',
        'power_source': '動力源',
        'warehouse_group': '倉庫グループ',
        'repair_target_type': '修繕対象種別',
        'repair_reason': '修繕理由',
        'asset_status': '資産ステータス',
        'ownership_type': '所有形態',
        'department': '部門',
        'manufacturer': 'メーカー',
        'warehouse_number': '倉庫番号',
        'floor': '階層',
        'operator': '取扱担当者'
    }
    category_name = category_names.get(category, category)
    
    return render_template('master/create.html', 
                          category=category, 
                          category_name=category_name)

@master_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """マスターデータの編集"""
    item = MasterItem.query.get_or_404(id)
    
    if request.method == 'POST':
        value = request.form.get('value')
        description = request.form.get('description')
        sort_order = request.form.get('sort_order', 0)
        is_active = 'is_active' in request.form
        
        # 必須項目の検証
        if not value:
            flash('値は必須項目です', 'danger')
            return redirect(request.url)
        
        try:
            # マスターアイテムを更新
            item.value = value
            item.description = description
            item.sort_order = int(sort_order) if sort_order else 0
            item.is_active = is_active
            
            db.session.commit()
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='update',
                entity_type='master_item',
                entity_id=item.id,
                operator=request.form.get('operator_name', 'システム'),
                details=f'マスターデータ {item.category}:{item.key} を更新'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('マスターデータが正常に更新されました', 'success')
            return redirect(url_for('master.category', category=item.category))
            
        except Exception as e:
            db.session.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    # カテゴリ名を取得
    category_names = {
        'forklift_type': 'フォークリフトタイプ',
        'power_source': '動力源',
        'warehouse_group': '倉庫グループ',
        'repair_target_type': '修繕対象種別',
        'repair_reason': '修繕理由',
        'asset_status': '資産ステータス',
        'ownership_type': '所有形態',
        'department': '部門',
        'manufacturer': 'メーカー',
        'warehouse_number': '倉庫番号',
        'floor': '階層',
        'operator': '取扱担当者'
    }
    category_name = category_names.get(item.category, item.category)
    
    return render_template('master/edit.html', 
                          item=item, 
                          category_name=category_name)

@master_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """マスターデータの削除"""
    item = MasterItem.query.get_or_404(id)
    category = item.category
    
    try:
        # 監査ログを記録
        audit_log = AuditLog(
            action='delete',
            entity_type='master_item',
            entity_id=item.id,
            operator=request.form.get('operator_name', 'システム'),
            details=f'マスターデータ {item.category}:{item.key} を削除'
        )
        db.session.add(audit_log)
        
        # マスターアイテムを削除
        db.session.delete(item)
        db.session.commit()
        
        flash('マスターデータが正常に削除されました', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('master.category', category=category))

@master_bp.route('/initialize', methods=['POST'])
@login_required
def initialize():
    """設定ファイルからマスターデータを初期化"""
    try:
        # フォークリフトタイプ
        for key, value in Config.FORKLIFT_TYPE_NAMES.items():
            if not MasterItem.query.filter_by(category='forklift_type', key=key).first():
                item = MasterItem(category='forklift_type', key=key, value=value)
                db.session.add(item)
        
        # 動力源
        for key, value in Config.POWER_SOURCE_NAMES.items():
            if not MasterItem.query.filter_by(category='power_source', key=key).first():
                item = MasterItem(category='power_source', key=key, value=value)
                db.session.add(item)
        
        # 修繕理由
        for key, value in Config.REPAIR_REASON_NAMES.items():
            if not MasterItem.query.filter_by(category='repair_reason', key=key).first():
                item = MasterItem(category='repair_reason', key=key, value=value)
                db.session.add(item)
        
        # 資産ステータス
        for key, value in Config.ASSET_STATUS_NAMES.items():
            if not MasterItem.query.filter_by(category='asset_status', key=key).first():
                item = MasterItem(category='asset_status', key=key, value=value)
                db.session.add(item)
        
        # 修繕対象種別
        for key, value in Config.REPAIR_TARGET_TYPE_NAMES.items():
            if not MasterItem.query.filter_by(category='repair_target_type', key=key).first():
                item = MasterItem(category='repair_target_type', key=key, value=value)
                db.session.add(item)
        
        # 所有形態
        for key, value in Config.OWNERSHIP_TYPE_NAMES.items():
            if not MasterItem.query.filter_by(category='ownership_type', key=key).first():
                item = MasterItem(category='ownership_type', key=key, value=value)
                db.session.add(item)
        
        # 部門
        for key, value in Config.DEPARTMENT_NAMES.items():
            if not MasterItem.query.filter_by(category='department', key=key).first():
                item = MasterItem(category='department', key=key, value=value)
                db.session.add(item)
        
        # メーカー
        for key, value in Config.MANUFACTURER_NAMES.items():
            if not MasterItem.query.filter_by(category='manufacturer', key=key).first():
                item = MasterItem(category='manufacturer', key=key, value=value)
                db.session.add(item)
        
        # 倉庫グループ
        for key, value in Config.WAREHOUSE_GROUP_NAMES.items():
            if not MasterItem.query.filter_by(category='warehouse_group', key=key).first():
                item = MasterItem(category='warehouse_group', key=key, value=value)
                db.session.add(item)
        
        # 倉庫番号
        for key, value in Config.WAREHOUSE_NUMBER_NAMES.items():
            if not MasterItem.query.filter_by(category='warehouse_number', key=key).first():
                item = MasterItem(category='warehouse_number', key=key, value=value)
                db.session.add(item)
        
        # 階層
        for key, value in Config.FLOOR_NAMES.items():
            if not MasterItem.query.filter_by(category='floor', key=key).first():
                item = MasterItem(category='floor', key=key, value=value)
                db.session.add(item)
        
        # 取扱担当者
        for key, value in Config.OPERATOR_NAMES.items():
            if not MasterItem.query.filter_by(category='operator', key=key).first():
                item = MasterItem(category='operator', key=key, value=value)
                db.session.add(item)
        
        db.session.commit()
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='initialize',
            entity_type='master_data',
            operator=request.form.get('operator_name', 'システム'),
            details='マスターデータを初期化'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('マスターデータが正常に初期化されました', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'エラーが発生しました: {str(e)}', 'danger')
    
    return redirect(url_for('master.index'))

@master_bp.route('/api/items/<category>')
def api_items(category):
    """特定のカテゴリのマスターデータをJSON形式で返す"""
    items = MasterItem.query.filter_by(category=category, is_active=True).order_by(MasterItem.sort_order, MasterItem.key).all()
    return jsonify([item.to_dict() for item in items])