from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            flash(f'✅ Welcome back, {username}!', 'success')
            return redirect(url_for('cloud.index'))
        else:
            flash('❌ Invalid username or password', 'warning')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if not username or not password:
            flash('❌ Username and password required', 'warning')
        elif password != confirm:
            flash('❌ Passwords do not match', 'warning')
        elif User.get_by_username(username):
            flash('❌ Username already exists', 'warning')
        else:
            User.create(username, password)
            flash('✅ Registration successful! Please login', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('✅ Logged out successfully', 'success')
    return redirect(url_for('auth.login'))
