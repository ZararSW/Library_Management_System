from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User
from forms import LoginForm, RegistrationForm, CreateAdminForm, EditProfileForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=False,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='Profile')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        if form.current_password.data:
            if check_password_hash(current_user.password_hash, form.current_password.data):
                current_user.username = form.username.data
                current_user.email = form.email.data
                
                if form.new_password.data:
                    current_user.password_hash = generate_password_hash(form.new_password.data)
                
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash('Current password is incorrect', 'danger')
        else:
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', title='Edit Profile', form=form)

@auth_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
def create_admin():
    if not current_user.is_admin:
        abort(403)
    
    form = CreateAdminForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        flash('Admin account created successfully!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/create_admin.html', title='Create Admin', form=form)

@auth_bp.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        abort(403)
    
    users = User.query.all()
    return render_template('auth/users.html', title='User Management', users=users)

@auth_bp.route('/users/<int:user_id>')
@login_required
def view_user(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    return render_template('auth/view_user.html', title='User Details', user=user)

@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('auth.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('auth.users'))
