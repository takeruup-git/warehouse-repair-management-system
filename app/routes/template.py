import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from app.models import db, AuditLog
from app.models.template import FormTemplate
from datetime import datetime

template_bp = Blueprint('template', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@template_bp.route('/')
def index():
    templates = FormTemplate.query.order_by(FormTemplate.created_at.desc()).all()
    return render_template('template/index.html', templates=templates)

@template_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # ファイルが選択されているか確認
        if 'template_file' not in request.files:
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        file = request.files['template_file']
        
        # ファイル名が空でないか確認
        if file.filename == '':
            flash('ファイルが選択されていません', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # ファイル名を安全に保存
            filename = secure_filename(file.filename)
            
            # 保存先ディレクトリの作成
            upload_dir = os.path.join(current_app.root_path, 'static', 'templates')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # タイムスタンプを付けてファイル名の重複を避ける
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{file_ext}"
            
            # ファイルを保存
            file_path = os.path.join(upload_dir, new_filename)
            file.save(file_path)
            
            # データベースに登録
            template = FormTemplate(
                name=request.form['name'],
                description=request.form.get('description', ''),
                file_path=os.path.join('static', 'templates', new_filename),
                form_type=request.form['form_type'],
                created_by=request.form.get('operator', 'システム'),
                cell_mapping=request.form.get('cell_mapping', '{}')
            )
            
            db.session.add(template)
            
            # 監査ログを記録
            audit_log = AuditLog(
                action='create',
                entity_type='form_template',
                entity_id=template.id,
                operator=request.form.get('operator', 'システム'),
                details=f'フォームテンプレート「{template.name}」を登録'
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            flash('テンプレートが正常にアップロードされました', 'success')
            return redirect(url_for('template.index'))
        
        flash('許可されていないファイル形式です', 'danger')
        return redirect(request.url)
    
    return render_template('template/upload.html')

@template_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    template = FormTemplate.query.get_or_404(id)
    
    if request.method == 'POST':
        template.name = request.form['name']
        template.description = request.form.get('description', '')
        template.form_type = request.form['form_type']
        template.is_active = 'is_active' in request.form
        
        # 新しいファイルがアップロードされた場合
        if 'template_file' in request.files and request.files['template_file'].filename != '':
            file = request.files['template_file']
            
            if allowed_file(file.filename):
                # 古いファイルを削除（オプション）
                old_file_path = os.path.join(current_app.root_path, template.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                
                # 新しいファイルを保存
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_ext = os.path.splitext(filename)[1]
                new_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{file_ext}"
                
                upload_dir = os.path.join(current_app.root_path, 'static', 'templates')
                file_path = os.path.join(upload_dir, new_filename)
                file.save(file_path)
                
                template.file_path = os.path.join('static', 'templates', new_filename)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='update',
            entity_type='form_template',
            entity_id=template.id,
            operator=request.form.get('operator', 'システム'),
            details=f'フォームテンプレート「{template.name}」を更新'
        )
        db.session.add(audit_log)
        
        db.session.commit()
        flash('テンプレートが更新されました', 'success')
        return redirect(url_for('template.index'))
    
    return render_template('template/edit.html', template=template)

@template_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    template = FormTemplate.query.get_or_404(id)
    
    # ファイルを削除
    file_path = os.path.join(current_app.root_path, template.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 監査ログを記録
    audit_log = AuditLog(
        action='delete',
        entity_type='form_template',
        entity_id=template.id,
        operator=request.form.get('operator', 'システム'),
        details=f'フォームテンプレート「{template.name}」を削除'
    )
    db.session.add(audit_log)
    
    # データベースから削除
    db.session.delete(template)
    db.session.commit()
    
    flash('テンプレートが削除されました', 'success')
    return redirect(url_for('template.index'))

@template_bp.route('/<int:id>/mapping', methods=['GET', 'POST'])
def mapping(id):
    template = FormTemplate.query.get_or_404(id)
    
    if request.method == 'POST':
        # フォームからセルマッピング情報を取得
        mapping_data = {}
        for field in request.form:
            if field.startswith('cell_'):
                field_name = field[5:]  # 'cell_' プレフィックスを削除
                mapping_data[field_name] = request.form[field]
        
        # JSONとして保存
        template.cell_mapping = json.dumps(mapping_data)
        
        # 監査ログを記録
        audit_log = AuditLog(
            action='update',
            entity_type='form_template_mapping',
            entity_id=template.id,
            operator=request.form.get('operator', 'システム'),
            details=f'フォームテンプレート「{template.name}」のマッピング情報を更新'
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        flash('マッピング情報が保存されました', 'success')
        return redirect(url_for('template.index'))
    
    # 現在のマッピング情報を取得
    current_mapping = {}
    if template.cell_mapping:
        try:
            current_mapping = json.loads(template.cell_mapping)
        except:
            pass
    
    # フォークリフトモデルのフィールド一覧を取得
    forklift_fields = [
        ('management_number', '管理番号'),
        ('manufacturer', 'メーカー'),
        ('model', '機種'),
        ('serial_number', '機番'),
        ('manufacture_date', '製造年月日'),
        ('load_capacity', '積載量'),
        ('lift_height', '揚高'),
        ('power_source_name', '動力'),
        ('warehouse_group', '倉庫グループ'),
        ('warehouse_number', '倉庫番号'),
        ('floor', 'フロア'),
        ('operator', '取扱担当者')
    ]
    
    return render_template('template/mapping.html', 
                          template=template, 
                          current_mapping=current_mapping,
                          forklift_fields=forklift_fields)