from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Application, Startup

investor_bp = Blueprint('investor', __name__, url_prefix='/investor')

@investor_bp.before_request
def require_investor():
    # 1. التأكد أنه مسجل دخول وأنه ممول
    if not current_user.is_authenticated or current_user.role != 'Investor':
        return redirect(url_for('auth.login'))
        
    # 2. الحماية الجديدة: منع الدخول إذا لم يتم توثيق السجل التجاري من الأدمن
    if current_user.verification_status != 'verified' and request.endpoint != 'dashboard.settings':
        flash('عذراً، يجب توثيق حسابك كمستثمر (برفع السجل التجاري) وموافقة الإدارة أولاً لتتمكن من الاطلاع على المشاريع.', 'warning')
        return redirect(url_for('dashboard.settings'))


@investor_bp.route('/portal')
@login_required
def portal():
    """عرض المشاريع المقبولة للتدريب مقسمة بالمدن"""
    # جلب الأفكار المقبولة (status='accepted') بدلاً من المتخرجة
    accepted_startups = Application.query.join(Startup).filter(Application.status == 'accepted').order_by(Startup.city).all()
    
    return render_template('investor/portal.html', apps=accepted_startups)

@investor_bp.route('/express-interest/<int:app_id>', methods=['POST'])
@login_required
def express_interest(app_id):
    """إرسال إشعار للمدرب والرائد باهتمام الممول"""
    app = Application.query.get_or_404(app_id)
    app.investor_id = current_user.id
    db.session.commit()
    flash("تم تسجيل اهتمامك بهذا المشروع! سيتم إشعار المدرب لترتيب التواصل.", "success")
    return redirect(url_for('investor.portal'))

from models import FundingMessage

@investor_bp.route('/contact-trainer/<int:app_id>', methods=['POST'])
@login_required
def contact_trainer(app_id):
    app = Application.query.get_or_404(app_id)
    message = request.form.get('message')
    
    msg = FundingMessage(investor_id=current_user.id, trainer_id=app.trainer_id, application_id=app.id, message=message)
    db.session.add(msg)
    db.session.commit()
    flash("تم إرسال رسالتك للمدرب المسؤول! سيتواصل معك قريباً.", "success")
    return redirect(url_for('investor.portal'))


from models import FundingMessage # تأكد من الاستيراد

@investor_bp.route('/project-details/<int:app_id>', methods=['GET', 'POST'])
@login_required
def project_details(app_id):
    """عرض تفاصيل الفكرة للممول ومراسلة المستشار"""
    app = Application.query.get_or_404(app_id)
    
    if request.method == 'POST':
        # الممول يرسل رسالة (ستظهر للمستشار)
        content = request.form.get('message_content')
        msg = FundingMessage(investor_id=current_user.id, application_id=app.id, message=content)
        db.session.add(msg)
        
        # ربط الممول بالمشروع كجهة تمويل محتملة
        app.investor_id = current_user.id
        db.session.commit()
        flash("تم إرسال طلب التمويل إلى المستشار بنجاح! سيتم التواصل معك قريباً.", "success")
        return redirect(url_for('investor.portal'))
        
    return render_template('investor/project_details.html', app=app)