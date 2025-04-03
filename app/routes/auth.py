from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from app.forms.auth import LoginForm, RegistrationForm, PasswordChangeForm
from datetime import datetime
import functools

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('この操作を行う権限がありません。', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager():
            flash('この操作を行う権限がありません。', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('このアカウントは無効化されています。管理者に連絡してください。', 'danger')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            flash(f'ようこそ、{user.username}さん！', 'success')
            return redirect(next_page)
        else:
            flash('ユーザー名またはパスワードが正しくありません。', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            full_name=form.full_name.data,
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        flash(f'ユーザー {user.username} が正常に登録されました！', 'success')
        return redirect(url_for('auth.user_list'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('auth/user_list.html', users=users)

@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = RegistrationForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash(f'ユーザー {user.username} の情報が更新されました！', 'success')
        return redirect(url_for('auth.user_list'))
    
    return render_template('auth/edit_user.html', form=form, user=user)

@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('自分自身を削除することはできません。', 'danger')
        return redirect(url_for('auth.user_list'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'ユーザー {user.username} が削除されました。', 'success')
    return redirect(url_for('auth.user_list'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('パスワードが正常に変更されました！', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('現在のパスワードが正しくありません。', 'danger')
    
    return render_template('auth/change_password.html', form=form)