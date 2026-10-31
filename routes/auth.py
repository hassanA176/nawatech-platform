from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def role_required(*roles):
    """Decorator لتقييد الوصول حسب الدور"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user and user.check_password(password):
            login_user(user)
            session['user_role'] = user.role
            flash(f'مرحباً {user.full_name}!', 'success')
            
            # توجيه حسب الدور
            if user.role == 'Admin':
                return redirect(url_for('dashboard.index'))
            elif user.role == 'Advisor':
                return redirect(url_for('advisor.inbox'))
            elif user.role == 'Trainer':
                return redirect(url_for('dashboard.index'))
            else:  # Founder
                return redirect(url_for('dashboard.index'))
        else:
            flash('بيانات الدخول غير صحيحة', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        role = request.form.get("role")
        city = request.form.get("city") # استلام المدينة

        if User.query.filter_by(email=email).first():
            flash("البريد الإلكتروني مسجل مسبقاً", "error")
            return redirect(url_for("auth.register"))

        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            city=city # حفظ المدينة
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('index'))
