from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Application, User, AdvisorMessage, Startup, SharedProject, FundingMessage, FormOneSubmission

advisor_bp = Blueprint('advisor', __name__, url_prefix='/advisor')

@advisor_bp.before_request
def require_advisor():
    if not current_user.is_authenticated or current_user.role != 'Advisor':
        return redirect(url_for('auth.login'))
    if current_user.verification_status != 'verified' and request.endpoint != 'dashboard.settings':
        return redirect(url_for('dashboard.settings'))

@advisor_bp.route('/')
@advisor_bp.route('/inbox')
@login_required
def inbox():
    """لوحة المستشار"""
# حل مشكلة اختلاف لغة المدن لجميع محافظات العراق
    city_map = {
        "بغداد": ["بغداد", "Baghdad"],
        "نينوى": ["نينوى", "Nineveh"],
        "البصرة": ["البصرة", "Basra"],
        "أربيل": ["أربيل", "Erbil"],
        "السليمانية": ["السليمانية", "Sulaymaniyah"],
        "بابل": ["بابل", "Babil"],
        "ذي قار": ["ذي قار", "Dhi Qar"],
        "الأنبار": ["الأنبار", "Anbar"],
        "ديالى": ["ديالى", "Diyala"],
        "كركوك": ["كركوك", "Kirkuk"],
        "النجف": ["النجف", "Najaf"],
        "كربلاء":["كربلاء", "Karbala"],
        "واسط": ["واسط", "Wasit"],
        "صلاح الدين":["صلاح الدين", "Salah Al-Din"],
        "القادسية":["القادسية", "القادسية / الديوانية", "Al-Qadisiyyah"],
        "ميسان": ["ميسان", "Maysan"],
        "المثنى": ["المثنى", "المثنى / السماوة", "Al-Muthanna"],
        "دهوك": ["دهوك", "Duhok"],
        "حلبجة":["حلبجة", "Halabja"]
    }
    allowed_cities = city_map.get(current_user.city,[current_user.city])

    # 1. الأفكار الـ VIP
    vip_ideas = Application.query.join(Startup).filter(
        Application.status == 'accepted', 
        Application.importance_level == 'high',
        Startup.city.in_(allowed_cities)
    ).all()
    
    # 2. المشاريع المرسلة من المدربين
    from models import SharedProject
    shared_projects = SharedProject.query.filter_by(advisor_id=current_user.id).order_by(SharedProject.created_at.desc()).all()
    
    # === طريقة آمنة جداً لحساب الإشعارات بدون انهيار ===
    unread_count = 0
    for p in shared_projects:
        # يتأكد أولاً أن العمود موجود في الداتا بيز
        if hasattr(p, 'is_read'):
            if not p.is_read:
                unread_count += 1
            p.is_read = True # تحويلها لمقروءة
    db.session.commit()
    
    # 3. جلب رسائل الممولين (طلبات التمويل)
    from models import FundingMessage
    funding_requests = FundingMessage.query.join(Application).join(Startup).filter(
        Startup.city.in_(allowed_cities)
    ).order_by(FundingMessage.created_at.desc()).all()
    
    all_trainers = User.query.filter_by(role='Trainer', verification_status='verified').all()
    
    return render_template('advisor/inbox.html', ideas=vip_ideas, shared_projects=shared_projects, unread_count=unread_count, funding_requests=funding_requests, trainers=all_trainers)
@advisor_bp.route('/project-details/<int:app_id>')
@login_required
def project_details(app_id):
    """المسار الجديد: عرض تفاصيل المشروع بالكامل للمستشار"""
    app = Application.query.get_or_404(app_id)
    form_one = FormOneSubmission.query.filter_by(application_id=app.id).first()
    return render_template('advisor/project_details.html', app=app, form_one=form_one)

@advisor_bp.route('/send-request', methods=['POST'])
@login_required
def send_request():
    """إرسال طلب للمدرب"""
    trainer_id = request.form.get('trainer_id')
    content = request.form.get('content')
    new_message = AdvisorMessage(advisor_id=current_user.id, trainer_id=trainer_id, content=content)
    db.session.add(new_message)
    db.session.commit()
    flash("تم إرسال طلبك للمدرب بنجاح!", "success")
    return redirect(url_for('advisor.inbox'))