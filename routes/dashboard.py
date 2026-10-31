from flask import (
    Blueprint,
    render_template,
    render_template_string,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
    send_from_directory,
    abort,
)

import google.generativeai as genai
import json
from flask import jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import datetime

from flask_login import login_required, current_user
from models import db, User, Startup, Application, Program
from werkzeug.utils import secure_filename
import os
import datetime
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.before_request
def require_login():
    # استثناء مهم: السماح للمساعد الذكي (smart-chat) بالعمل مع الزوار
    if request.endpoint and 'smart_chat' in request.endpoint:
        return None  # لا تفرض تسجيل الدخول

    # باقي الروتات تحتاج تسجيل دخول
    if not current_user.is_authenticated:
        flash("يجب تسجيل الدخول أولاً", "info")
        return redirect(url_for("auth.login"))


@dashboard_bp.route("/")
@login_required
def index():
    """لوحة التحكم الرئيسية"""

    # 1. توجيه الأدوار الخاصة إلى لوحاتهم (كل لوحة محمية بالتوثيق من داخل ملفها)
    if current_user.role == "Trainer":
        return redirect(url_for("trainer.dashboard"))
    elif current_user.role == "Advisor":
        return redirect(url_for("advisor.inbox"))
    elif current_user.role == "Investor":
         return redirect(url_for("investor.portal"))

    # ==========================================
    # 2. الحل الجذري: إجبار الرائد على التوثيق فوراً
    # ==========================================
    if current_user.role == "Founder":
        if current_user.verification_status in['unverified', 'rejected']:
            flash("تنبيه: يجب عليك رفع صورة الهوية الوطنية وتوثيق حسابك أولاً لتتمكن من استخدام المنصة والتقديم على البرامج.", "warning")
            return redirect(url_for("dashboard.settings"))

    try:
        # ====== 3. كود الإدارة (Admin) ======
        if current_user.role == "Admin":
            stats = {
                "total_users": User.query.count(),
                "total_startups": Startup.query.count(),
                "total_programs": Program.query.count(),
                "active_applications": Application.query.count(),
            }
            
            return render_template_string("""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>لوحة الإدارة - نواتك</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }
                    .navbar { background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%); }
                    .stats-card { background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 2rem; border-bottom: 4px solid #1a237e;}
                </style>
            </head>
            <body>
                <nav class="navbar navbar-dark">
                    <div class="container">
                        <a class="navbar-brand fw-bold" href="/"><i class="fas fa-rocket text-warning me-2"></i>نواتك - الإدارة</a>
                        <a class="nav-link text-white fw-bold" href="/logout"><i class="fas fa-sign-out-alt me-1"></i>خروج</a>
                    </div>
                </nav>

                <div class="container mt-5 mb-5">
                    <div class="text-center mb-5">
                        <h1 class="fw-bold text-dark">لوحة التحكم الرئيسية</h1>
                        <p class="lead text-muted">مرحباً بك مدير النظام - {{ current_user.full_name }}</p>
                    </div>
                    
                    <div class="row g-4">
                        <div class="col-md-3">
                            <div class="stats-card text-center"><i class="fas fa-users fa-3x text-primary mb-3"></i><h2 class="fw-bold">{{ stats.total_users }}</h2><p class="text-muted fw-bold mb-0">المستخدمين</p></div>
                        </div>
                        <div class="col-md-3">
                            <div class="stats-card text-center"><i class="fas fa-lightbulb fa-3x text-warning mb-3"></i><h2 class="fw-bold">{{ stats.total_startups }}</h2><p class="text-muted fw-bold mb-0">الأفكار الناشئة</p></div>
                        </div>
                        <div class="col-md-3">
                            <div class="stats-card text-center"><i class="fas fa-graduation-cap fa-3x text-success mb-3"></i><h2 class="fw-bold">{{ stats.total_programs }}</h2><p class="text-muted fw-bold mb-0">البرامج النشطة</p></div>
                        </div>
                        <div class="col-md-3">
                            <div class="stats-card text-center"><i class="fas fa-layer-group fa-3x text-info mb-3"></i><h2 class="fw-bold">{{ stats.active_applications }}</h2><p class="text-muted fw-bold mb-0">إجمالي الطلبات</p></div>
                        </div>
                        <div class="col-md-3"><a href="/dashboard/services-management" class="btn btn-dark btn-lg w-100 fw-bold shadow-sm"><i class="fas fa-briefcase me-2"></i>إدارة الخدمات</a></div>
                        <div class="col-md-3"><a href="{{ url_for('dashboard.purchases') }}" class="btn btn-outline-success"><i class="fas fa-list me-2"></i>عرض سجل الدفعات</a></div>

                    </div>
                    
                    <div class="row mt-4 g-3">
                        <div class="col-md-4"><a href="/dashboard/users" class="btn btn-primary btn-lg w-100 fw-bold shadow-sm"><i class="fas fa-users me-2"></i>إدارة المستخدمين</a></div>
                        <div class="col-md-4"><a href="/dashboard/applications" class="btn btn-warning text-dark btn-lg w-100 fw-bold shadow-sm"><i class="fas fa-eye me-2"></i>رؤية الأفكار المقدمة</a></div>
                        <div class="col-md-4"><a href="/dashboard/programs-management" class="btn btn-success btn-lg w-100 fw-bold shadow-sm"><i class="fas fa-graduation-cap me-2"></i>إدارة البرامج</a></div>
                    </div>
                </div>
            </body>
            </html>
            """, stats=stats, current_user=current_user)

        # ====== 4. كود رائد الأعمال (Founder) ======
        else:  
            my_applications = Application.query.join(Startup).filter(Startup.owner_user_id == current_user.id).order_by(Application.created_at.desc()).all()
            open_programs = Program.query.filter_by(status='open').order_by(Program.start_date.desc()).all()
            
            # حساب التقدم للرائد
            for app in my_applications:
                if app.status == 'accepted':
                    total_prep = len(PREP_COURSE)
                    from models import TrainerCourse
                    trainer_courses = TrainerCourse.query.filter_by(trainer_id=app.trainer_id, program_id=app.program_id).all()
                    trainer_lessons_count = sum([len(c.lessons) for c in trainer_courses])
                    
                    total_lessons = total_prep + trainer_lessons_count
                    completed_count = LessonProgress.query.filter_by(application_id=app.id).count()
                    app.progress_percent = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0
            
            stats = {
                "applications_count": len(my_applications),
                "startups_count": Startup.query.filter_by(owner_user_id=current_user.id).count(),
                "accepted_count": len([app for app in my_applications if app.status == 'accepted'])
            }

            return render_template("dashboard/founder.html", stats=stats, my_applications=my_applications, programs=open_programs)

    except Exception as e:
        print(f"Error in Dashboard Index: {e}")
        # الحماية من انهيار الصفحة في حال وجود خطأ في البيانات
        if current_user.role == "Admin":
            return redirect(url_for('dashboard.users'))
        
        fallback_stats = {"applications_count":0, "startups_count":0, "accepted_count":0}
        
        # السطر الذي كان مفقوداً بالكامل:
        return render_template("dashboard/founder.html", stats=fallback_stats, my_applications=[], programs=[]
            )
import google.generativeai as genai
import json
from flask import jsonify
from models import LessonProgress # تأكد من استيراده في الأعلى

# تأكد من استيراد الكلاس الجديد
from models import db, User, Startup, Program, StartupEvaluation 
# ==========================================
# مسارات تشغيل الملفات المحلية (فيديوهات + PDF)
# ==========================================
@dashboard_bp.route('/media/videos/<path:filename>')
@login_required
def serve_video(filename):
    """قراءة الفيديوهات والترجمات من مجلد videos"""
    video_dir = os.path.join(current_app.root_path, 'videos')
    return send_from_directory(video_dir, filename)

import os

@dashboard_bp.route('/media/pdf/<path:filename>')
@login_required
def serve_pdf(filename):
    """قراءة ملف الـ PDF الخاص بالمكتبة ومشروع التخرج من المسار الرئيسي"""
    # جلب المسار الجذري الفعلي للمشروع بشكل دقيق
    project_root = os.path.abspath(current_app.root_path)
    
    # إرسال الملف من هذا المسار
    return send_from_directory(project_root, filename)

# ==========================================
# بيانات الكورس التحضيري (الفيديوهات المحلية)
# ==========================================
PREP_COURSE =[
    {
        "id": "prep_1",
        "title": "مقدمة في تطوير الأعمال",
        "video_url": "/dashboard/media/videos/vid_one.mp4",
        "subtitle_url": "/dashboard/media/videos/subtitles-enone.vtt",
        "content": "مرحباً بك في الكورس التحضيري! في هذا الدرس الافتتاحي، سنتعرف على المفهوم الأساسي لتطوير الأعمال.",
        "quiz": {"question": "ما هو الهدف الأساسي من تطوير الأعمال؟", "options":["زيادة المبيعات الفورية", "خلق قيمة طويلة الأمد للمؤسسة", "إدارة الموارد البشرية", "تصميم شعار الشركة"], "correct": 1}
    },
    {
        "id": "prep_2",
        "title": "مقدمة وأمثلة عملية",
        "video_url": "/dashboard/media/videos/vid_two.mp4", 
        "subtitle_url": "/dashboard/media/videos/subtitles-en (1).vtt",
        "content": "في هذا الدرس، نتعمق أكثر من خلال أمثلة حية لشركات قامت بتطبيق استراتيجيات تطوير الأعمال.",
        "quiz": {"question": "تطوير الأعمال يعتمد بشكل كبير على:", "options":["بناء شراكات استراتيجية وعلاقات", "البرمجة وكتابة الأكواد", "الصيانة الدورية للآلات", "الرد على الشكاوى فقط"], "correct": 0}
    },
    {
        "id": "prep_3",
        "title": "متى يتم تطبيق تطوير الأعمال؟",
        "video_url": "/dashboard/media/videos/vid_three.mp4",
        "subtitle_url": "/dashboard/media/videos/subtitles-en (2).vtt",
        "content": "متى يجب على الشركة أن تبدأ في تطوير أعمالها؟ سنتعرف على التوقيت المناسب.",
        "quiz": {"question": "هل يقتصر تطوير الأعمال على الشركات الكبيرة فقط؟", "options":["نعم، لأنها تمتلك المال", "لا، يمكن تطبيقه في الشركات الناشئة أيضاً", "نعم، الشركات الصغيرة لا تحتاجه", "يقتصر على الشركات التقنية فقط"], "correct": 1}
    }
]
@dashboard_bp.route("/startup/<int:startup_id>")
@login_required
def startup_detail(startup_id):
    """عرض تفاصيل الفكرة (لحل خطأ BuildError)"""
    startup = Startup.query.get_or_404(startup_id)
    if startup.owner_user_id != current_user.id:
        flash("غير مصرح لك بعرض هذه الشركة", "error")
        return redirect(url_for("dashboard.index"))
    return render_template("dashboard/startup_detail.html", startup=startup)
@dashboard_bp.route("/learning/<int:app_id>")
@login_required
def learning_hub(app_id):
    application = Application.query.get_or_404(app_id)
    if application.startup.owner_user_id != current_user.id or application.status != 'accepted':
        return redirect(url_for('dashboard.index'))
    
    completed_lessons =[p.lesson_id for p in LessonProgress.query.filter_by(application_id=app_id).all()]
    
    # تجهيز كورسات المدرب بصيغة يقرأها الجافاسكربت
    from models import TrainerCourse 
    trainer_courses = TrainerCourse.query.filter_by(trainer_id=application.trainer_id, program_id=application.program_id).all()
    t_courses_data =[]
    for c in trainer_courses:
        lessons_data =[]
        for l in c.lessons:
            lessons_data.append({
                'id': str(l.id), 'title': l.title,
                'text': l.text_content, 'video': l.video_path, 'pdf': l.pdf_path,
                'image': l.image_path, 'link': l.link_url
            })
        t_courses_data.append({'id': c.id, 'title': c.title, 'lessons': lessons_data})
        
    return render_template("dashboard/learning.html", app=application, prep_course=PREP_COURSE, completed_lessons=completed_lessons, trainer_courses=t_courses_data)

import datetime # نضعها هنا احتياطياً لضمان عملها

@dashboard_bp.route("/certificate/<int:app_id>")
@login_required
def view_certificate(app_id):
    """عرض الشهادة للرائد بعد التخرج"""
    app = Application.query.get_or_404(app_id)
    if app.startup.owner_user_id != current_user.id or not app.is_graduated:
        return redirect(url_for('dashboard.index'))
    
    # التعديل هنا: تمت إضافة .datetime. لتعمل بدون أي أخطاء
    today_date = datetime.datetime.now().strftime('%Y/%m/%d')
    
    return render_template("dashboard/certificate.html", app=app, today=today_date)
@dashboard_bp.route("/api/mark-lesson", methods=['POST'])
@login_required
def mark_lesson_complete():
    """حفظ تقدم الرائد في الداتا بيز"""
    data = request.get_json()
    app_id = data.get('app_id')
    lesson_id = data.get('lesson_id')
    
    existing = LessonProgress.query.filter_by(application_id=app_id, lesson_id=lesson_id).first()
    if not existing:
        new_progress = LessonProgress(application_id=app_id, lesson_id=lesson_id)
        db.session.add(new_progress)
        db.session.commit()
    return jsonify({"status": "success"})
# إعداد مفتاح API (يفضل وضعه في ملف .env)
# استبدل النص التالي بمفتاحك الحقيقي

import google.generativeai as genai
import json
from flask import jsonify, request, flash, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user
# تأكد من استيراد النماذج بشكل صحيح حسب هيكلة ملفاتك
from models import db, Startup, Program, StartupEvaluation

# إعداد مفتاح API (يفضل وضعه في متغيرات البيئة)
GENAI_API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GENAI_API_KEY) if GENAI_API_KEY else None


import os
from werkzeug.utils import secure_filename
from flask import request, flash, redirect, url_for, current_app


# أضف هذه الاستيرادات في الأعلى إذا لم تكن موجودة
from models import SharedProject 
import json
ai_client = genai.configure(api_key=GENAI_API_KEY) if GENAI_API_KEY else None


@dashboard_bp.route("/api/smart-chat", methods=['POST'])
# تم حذف @login_required لكي يعمل المساعد مع الزوار غير المسجلين
def smart_chat():
    """عقل المساعد الذكي: يجيب للزوار وللمستخدمين المسجلين"""
    data = request.get_json()
    user_msg = data.get('message', '')
    chat_history = data.get('history', [])
    
    if not user_msg:
        return jsonify({'error': 'رسالة فارغة'}), 400

    # تحديد اسم المستخدم (زائر أو مستخدم مسجل)
    user_name = current_user.full_name if current_user.is_authenticated else "الزائر الكريم"

    # 1. الشخصية الأساسية (نبقيها كما هي مع تعديل بسيط لدعم الزائر)
    system_instruction = f"""
    أنت 'نواتك AI'، خبير متخصص في ريادة الأعمال، ومستشار ذكي، وروبوت محادثة ودود يعمل في 'حاضنة نواتك للريادة والابتكار'.
    تتحدث باللغة العربية بأسلوب احترافي ومحفز. 
    مسموح لك تماماً باستخدام معرفتك الواسعة في إدارة الأعمال، نماذج العمل، التسويق، والتقنية لمساعدة المستخدم.
    الاسم الذي تتحدث معه الآن هو: {user_name}.
    """

    context_data = ""

    # ==========================================
    # حالة الزائر (الجزء الجديد)
    # ==========================================
    if not current_user.is_authenticated:
        context_data = f"""
        دور المستخدم: زائر يتصفح الموقع (ليس لديه حساب بعد).
        معلومات عن حاضنة نواتك (Nawatech):
        هي حاضنة أعمال رقمية مملوكة لشركة BUTTERBOOK SDN. BHD الماليزية. نهدف لدعم رواد الأعمال في الشرق الأوسط.
        نوفر: تدريب متخصص، إرشاد مباشر من خبراء، تقييم بالذكاء الاصطناعي، وربط مع مستثمرين حقيقيين.
        
        مهمتك مع الزائر:
        - أجب عن أسئلته حول ريادة الأعمال بشكل عام.
        - اقنعه وحفزه بشدة لإنشاء حساب في المنصة كـ "رائد أعمال" للبدء في رحلته، أو كـ "مستثمر" لرؤية المشاريع.
        - كن لبقاً، وإذا سأل كيف يبدأ، أخبره أن يضغط على زر "إنشاء حساب" أو "سجل معنا الآن".
        """

    # ==========================================
    # حالة المستخدم المسجل (نبقي المنطق القديم كما هو تماماً)
    # ==========================================
    else:
        if current_user.role == 'Founder':
            # بيانات الرائد (الكود الأصلي بدون أي تغيير)
            my_apps_query = Application.query.join(Startup).filter(Startup.owner_user_id == current_user.id).all()
            programs = Program.query.filter_by(status='open').all()
            
            apps_info = "\n".join([f"- مشروع '{a.startup.name}' في برنامج '{a.program.name}' (الحالة: {a.status}، إنجاز الكورسات: {getattr(a, 'progress_percent', 0)}%)" for a in my_apps_query])
            progs_info = "\n".join([f"- {p.name} (المدينة: {p.city})" for p in programs])
            
            context_data = f"""
            دور المستخدم: رائد أعمال (Founder).
            بيانات المنصة الخاصة به:
            مشاريعه: {apps_info if apps_info else 'ليس لديه مشاريع مقدمة حتى الآن.'}
            البرامج المتاحة للتقديم الآن: {progs_info if progs_info else 'لا توجد برامج مفتوحة.'}
            
            تعليماتك الخاصة مع الرائد: 
            - إذا سأل عن مشاريعه، استخدم البيانات أعلاه.
            - إذا سأل عن كيفية التقديم، ساعده في العصف الذهني! اقترح عليه أفكاراً، ساعده في صياغة (المشكلة، الحل، السوق المستهدف، الميزة التنافسية).
            - إذا طلب منك مراجعة نص كتبه، قم بتنقيحه وجعله يبدو أكثر احترافية وجاذبية للمستثمرين.
            - كن موجهاً وداعماً له في كل خطوات تأسيس شركته الناشئة.
            """
            
        elif current_user.role == 'Trainer':
            my_startups = Application.query.filter_by(trainer_id=current_user.id, status='accepted').all()
            startups_info = [f"- مشروع '{app.startup.name}' (الرائد '{app.startup.owner.full_name}'). التقييم: {app.startup.evaluation.total_score if app.startup.evaluation else 0}%." for app in my_startups]
                
            context_data = f"""
            دور المستخدم: مدرب معتمد في الحاضنة.
            المشاريع التي يدربها: {" ".join(startups_info) if startups_info else 'لا يشرف على مشاريع حالياً.'}
            
            تعليماتك الخاصة مع المدرب:
            - ساعده في طرق تقييم المشاريع، كيف يقرأ مصفوفات المخاطر، وكيف يضع خططاً تدريبية للرواد.
            - يمنع التحدث أو إعطاء معلومات عن مشاريع مدربين آخرين.
            """
            
        elif current_user.role == 'Advisor':
            vip_ideas = Application.query.filter_by(status='accepted', importance_level='high').all()
            vip_info = [f"- مشروع '{app.startup.name}' للمدرب '{app.trainer.full_name}'. التقييم: {app.startup.evaluation.total_score if app.startup.evaluation else 0}%." for app in vip_ideas]
                
            context_data = f"""
            دور المستخدم: مستشار استثماري وريادي.
            الأفكار VIP الحالية: {" ".join(vip_info) if vip_info else 'لا توجد أفكار VIP حالياً.'}
            
            تعليماتك الخاصة مع المستشار:
            - ساعده في تحليل الأفكار بعمق من ناحية العائد على الاستثمار (ROI)، قابلية التوسع، والمخاطر.
            """
            
        elif current_user.role == 'Investor':
            context_data = f"""
            دور المستخدم: جهة تمويل / مستثمر.
            تعليماتك الخاصة:
            - اشرح له كيف يمكنه تصفح المشاريع في المنصة واستخدام زر 'طلب الاستثمار'.
            - ساعده في فهم معايير التقييم التي تستخدمها الحاضنة لتقليل المخاطر على المستثمرين.
            """

    # 3. إعداد الذاكرة (نفس الطريقة الأصلية مع تحسين بسيط)
    history_text = ""
    if chat_history:
        history_text = "\n[سياق المحادثة السابقة لتتذكر ما تحدثتم عنه]:\n"
        for msg in chat_history:
            role = "المستخدم" if msg.get("role") == "user" else "أنت"
            history_text += f"{role}: {msg.get('text')}\n"

    # 4. تجميع الـ Prompt النهائي (نفس الهيكل الأصلي)
    full_prompt = f"""
    {system_instruction}
    
    [المعلومات المتوفرة لديك الآن]:
    {context_data}
    {history_text}
    
    [سؤال المستخدم الجديد]:
    {user_msg}
    
    الرد: (استخدم تنسيق HTML بسيط مثل <br>، <b>، أو <ul> عند الحاجة ليكون الرد مرتباً ومقروءاً).
    """

    try:
        # المشروع يستخدم مكتبة google.generativeai القديمة بالفعل،
        # لذلك نستخدم GenerativeModel بدل genai.Client الخاص بمكتبة google-genai الجديدة.
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(full_prompt)

        reply_text = (
            response.text
            .replace('```html', '')
            .replace('```', '')
            .strip()
        )
        return jsonify({'status': 'success', 'reply': reply_text})

    except Exception:
        # يطبع الـ traceback كاملًا في journalctl لتسهيل معرفة أي خطأ لاحق.
        current_app.logger.exception("Smart Chat AI Error")
        return jsonify({
            'status': 'error',
            'reply': 'عذراً، واجهت مشكلة تقنية في الاتصال بالشبكة. حاول مجدداً بعد قليل.'
        })
# دالة مساعدة لحفظ الملفات (تأكد من وجودها أو ضعها في الكود)
def save_file(file, folder):
    if file and file.filename:
        filename = secure_filename(file.filename)
        # تأكد من إنشاء المجلد مسبقاً
        save_path = os.path.join(current_app.root_path, 'static', 'uploads', folder)
        os.makedirs(save_path, exist_ok=True)
        file.save(os.path.join(save_path, filename))
        return os.path.join(folder, filename) # حفظ المسار النسبي
    return None

# تأكد من استدعاء genai وموديل التقييم
# import google.generativeai as genai

@dashboard_bp.route("/apply-program/<int:program_id>", methods=['GET', 'POST'])
@login_required
def apply_program(program_id):
    """صفحة التقديم على البرنامج (وتتضمن إنشاء فكرة المشروع والنموذج الأولي)"""
    
    if current_user.role != "Founder":
        flash("هذه الصفحة مخصصة لرواد الأعمال فقط", "error")
        return redirect(url_for("dashboard.index"))
    if current_user.verification_status not in['pending', 'verified']:
        flash("يجب عليك رفع صورة الهوية الوطنية وتوثيق حسابك قبل التقديم على البرامج.", "warning")
        return redirect(url_for("dashboard.settings"))

    program = Program.query.get_or_404(program_id)

    if request.method == "POST":
        try:
            # 1. جمع بيانات الفكرة
            name = request.form.get("name", "").strip()
            sector = request.form.get("sector")
            city = request.form.get("city")
            problem = request.form.get("problem", "").strip()
            solution = request.form.get("solution", "").strip()
            target_market = request.form.get("target_market", "").strip()
            summary = request.form.get("summary", "").strip()
            stage = "Idea"

            # 2. معالجة النموذج الأولي
            prototype_type = request.form.get("prototype_type", "builder") 
            prototype_path = None 
            prototype_data = None 

            if prototype_type == "upload":
                if 'prototype_file' in request.files:
                    file = request.files['prototype_file']
                    if file and file.filename:
                        timestamp = int(datetime.utcnow().timestamp())
                        filename = secure_filename(f"deck_{current_user.id}_{timestamp}_{file.filename}")
                        save_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'prototypes')
                        os.makedirs(save_dir, exist_ok=True)
                        file.save(os.path.join(save_dir, filename))
                        prototype_path = os.path.join('uploads', 'prototypes', filename)
            else:
                prototype_data = request.form.get("prototype_data")

            # 3. حفظ الفكرة (Startup)
            new_startup = Startup(
                owner_user_id=current_user.id,
                name=name,
                sector=sector,
                stage=stage,
                city=city,
                summary=summary,
                problem=problem,
                solution=solution,
                target_market=target_market,
                prototype_type=prototype_type,
                prototype_path=prototype_path,
                prototype_data=prototype_data 
            )
            db.session.add(new_startup)
            db.session.flush() # للحصول على الـ ID

            # 4. إنشاء طلب التقديم (Application)
            new_application = Application(
                startup_id=new_startup.id,
                program_id=program.id,
                status='submitted'
            )
            db.session.add(new_application)
            db.session.commit()

            # 5. التقييم الذكي (AI)
            prompt = f"""
            تصرف كخبير استشاري لتقييم فكرة مشروع.
            الاسم: {name} | القطاع: {sector} | المشكلة: {problem} | الحل: {solution} | السوق: {target_market} | الملخص: {summary}
            الرد بـ JSON فقط يحتوي على:
            {{"idea_score": (0-25), "tech_score": (0-25), "market_score": (0-25), "team_score": (0-25), "analysis_summary": "تحليل مختصر", "recommendation": "نصيحة"}}
            """
            
            try:
                model = genai.GenerativeModel('gemini-2.5-flash-lite')
                response = model.generate_content(prompt)
                json_str = response.text.replace('```json', '').replace('```', '').strip()
                eval_data = json.loads(json_str)
                total = sum([eval_data.get(k, 0) for k in ['idea_score', 'tech_score', 'market_score', 'team_score']])

                evaluation = StartupEvaluation(
                    startup_id=new_startup.id,
                    idea_score=eval_data.get('idea_score', 0),
                    team_score=eval_data.get('team_score', 0),
                    market_score=eval_data.get('market_score', 0),
                    tech_score=eval_data.get('tech_score', 0),
                    total_score=total,
                    analysis_summary=eval_data.get('analysis_summary', ''),
                    recommendation=eval_data.get('recommendation', '')
                )
                db.session.add(evaluation)
                db.session.commit()

                return jsonify({'status': 'success', 'message': 'تم تقديم الطلب', 'evaluation': eval_data, 'total_score': total})
            except Exception as ai_error:
                return jsonify({'status': 'success', 'message': 'تم التقديم (التحليل غير متاح)', 'evaluation': {'idea_score':0,'tech_score':0,'market_score':0,'team_score':0,'analysis_summary':'تم الحفظ بنجاح.','recommendation':'سيتم المراجعة.'}, 'total_score': 0})

        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f"حدث خطأ: {str(e)}"}), 500

    return render_template("dashboard/apply.html", program=program)


from flask import send_from_directory, current_app
import os

# روت جديد لعرض الملفات المرفوعة (صور + PDF)
import os
from flask import send_from_directory

# روت خاص لخدمة الملفات من مجلد uploads (خارج static)
import os
from flask import send_from_directory

@dashboard_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """يخدم الملفات من مجلد uploads/ids/ids"""
    
    # المسار الأساسي للمجلد
    base_dir = r"C:\Users\Lenovo\Desktop\araq-main\rafidain_incubator\uploads"
    
    # تصحيح تلقائي للتكرار ids/ids
    if filename.startswith("uploads/ids/"):
        filename = filename.replace("uploads/ids/", "ids/ids/", 1)
    elif not filename.startswith("ids/ids/"):
        filename = os.path.join("ids/ids", filename)
    
    try:
        return send_from_directory(base_dir, filename)
    except FileNotFoundError:
        return "الملف غير موجود", 404
@dashboard_bp.route("/users")
@login_required
def users():
    """إدارة المستخدمين - للأدمن فقط (عرض الهويات + الحظر + الحذف + التعديل)"""
    if current_user.role != "Admin":
        return redirect(url_for("dashboard.index"))

    users_list = User.query.order_by(User.created_at.desc()).all()
    users_html = ""
    
    for user in users_list:
        role_badge = {
            "Admin": '<span class="badge bg-danger">مدير</span>',
            "Advisor": '<span class="badge bg-success">مستشار</span>',
            "Trainer": '<span class="badge bg-info text-dark">مدرب</span>',
            "Founder": '<span class="badge bg-primary">رائد أعمال</span>',
            "Investor": '<span class="badge bg-warning text-dark">جهة تمويل</span>',
        }.get(user.role, '<span class="badge bg-secondary">غير محدد</span>')

        active_badge = '<span class="badge bg-success">نشط</span>' if user.is_active else '<span class="badge bg-danger">محظور</span>'
        ban_btn_text = "إلغاء الحظر" if not user.is_active else "حظر"
        ban_btn_color = "success" if not user.is_active else "warning"

        # ==========================================
        # 1. برمجة زر عرض الوثائق بالمسارات الدقيقة
        # ==========================================
        doc_btn = ""
        if user.verification_status != 'unverified':
            if user.role == 'Investor' and user.commercial_register_path:
                cr_path = user.commercial_register_path.replace('\\', '/')
                doc_btn = f'<a href="/{cr_path}" target="_blank" class="btn btn-sm btn-info text-dark fw-bold shadow-sm" title="عرض السجل التجاري"><i class="fas fa-file-pdf"></i> السجل</a>'
            
            elif user.id_front_path and user.id_back_path:
                # حل مشكلة المسار: إجبار الكود على استخدام الدالة الآمنة مباشرة
                doc_btn = f"""<button type="button" class="btn btn-sm btn-primary fw-bold shadow-sm" onclick="showIdModal('/dashboard/view-id-image/{user.id}/front', '/dashboard/view-id-image/{user.id}/back')"><i class="fas fa-id-card"></i> عرض الهوية</button>"""

        # تنظيف اسم المستخدم ورقم الهاتف لمنع أخطاء الجافاسكربت في زر التعديل
        safe_name = user.full_name.replace("'", "\\'") if user.full_name else ""
        safe_phone = user.phone.replace("'", "\\'") if user.phone else ""

        # ==========================================
        # 2. أزرار الإجراءات
        # ==========================================
        admin_actions = f"""
            <div class="d-flex gap-1">
                {doc_btn}
                <button type="button" class="btn btn-sm btn-outline-dark fw-bold" title="تعديل" onclick="editUser({user.id}, '{safe_name}', '{safe_phone}')"><i class="fas fa-edit"></i></button>
                
                <form action="/dashboard/toggle-user/{user.id}" method="POST" style="display:inline;">
                    <button type="submit" class="btn btn-sm btn-{ban_btn_color} text-dark fw-bold" title="{ban_btn_text}" onclick="return confirm('هل أنت متأكد من تغيير حالة المستخدم؟')"><i class="fas fa-ban"></i></button>
                </form>

                <form action="/dashboard/delete-user/{user.id}" method="POST" style="display:inline;">
                    <button type="submit" class="btn btn-sm btn-danger fw-bold shadow-sm" title="حذف نهائي" onclick="return confirm('تنبيه خطير: هل أنت متأكد من حذف هذا المستخدم نهائياً؟ سيتم مسح كل بياناته!')"><i class="fas fa-trash-alt"></i></button>
                </form>
            </div>
        """

        if user.verification_status == "pending":
            admin_actions += f"""
                <div class="mt-2">
                    <a href="/dashboard/approve-verification/{user.id}" class="btn btn-sm btn-success fw-bold w-100"><i class="fas fa-check-circle"></i> توثيق الحساب الآن</a>
                </div>
            """

        users_html += f"""
        <tr>
            <td class="fw-bold text-dark">{user.full_name} <br><small class="text-muted" style="font-family: Arial;">{user.email}</small></td>
            <td>{role_badge}</td>
            <td><span class="badge bg-{'success' if user.verification_status == 'verified' else 'danger' if user.verification_status == 'rejected' else 'secondary'}">{user.verification_status}</span></td>
            <td>{active_badge}</td>
            <td>{admin_actions}</td>
        </tr>
        """

    # ==========================================
    # 3. واجهة الـ HTML 
    # ==========================================
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <title>إدارة المستخدمين - الإدارة</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
        <style>body {{ background:#f4f6f9; font-family: 'Cairo', sans-serif; }}</style>
    </head>
    <body>
        <div class="container mt-5 mb-5">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2 class="fw-bold text-dark"><i class="fas fa-users-cog text-primary me-2"></i> إدارة المستخدمين والتوثيق</h2>
                <a href="/dashboard" class="btn btn-dark fw-bold px-4">العودة للوحة الإدارة</a>
            </div>

            {{% with messages = get_flashed_messages(with_categories=true) %}}
                {{% if messages %}}
                    {{% for category, message in messages %}}
                        <div class="alert alert-{{{{ 'success' if category == 'success' else 'danger' }}}} fw-bold">{{{{ message }}}}</div>
                    {{% endfor %}}
                {{% endif %}}
            {{% endwith %}}

            <div class="card shadow-lg border-0 rounded-4 overflow-hidden">
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead class="bg-dark text-white">
                                <tr>
                                    <th class="py-3 px-4">اسم المستخدم والبريد</th>
                                    <th class="py-3">الدور</th>
                                    <th class="py-3">حالة التوثيق</th>
                                    <th class="py-3">حالة الدخول</th>
                                    <th class="py-3 px-4">الإجراءات</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal عرض الهوية -->
        <div class="modal fade" id="idModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg rounded-4">
                    <div class="modal-header bg-primary text-white border-0 py-3">
                        <h5 class="modal-title fw-bold"><i class="fas fa-id-card me-2"></i> الوثائق الرسمية للمستخدم</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center bg-light p-4">
                        <div class="row g-4">
                            <div class="col-md-6">
                                <h5 class="fw-bold text-dark mb-3">الوجه الأمامي</h5>
                                <div class="bg-white p-2 rounded-3 shadow-sm border">
                                    <img id="imgFront" src="" class="img-fluid rounded" style="max-height: 300px; object-fit: contain;">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h5 class="fw-bold text-dark mb-3">الوجه الخلفي</h5>
                                <div class="bg-white p-2 rounded-3 shadow-sm border">
                                    <img id="imgBack" src="" class="img-fluid rounded" style="max-height: 300px; object-fit: contain;">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer bg-white border-0">
                        <button type="button" class="btn btn-secondary fw-bold px-4" data-bs-dismiss="modal">إغلاق</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal تعديل بيانات المستخدم -->
        <div class="modal fade" id="editModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg rounded-4">
                    <form id="editForm" method="POST">
                        <div class="modal-header bg-dark text-white border-0 py-3">
                            <h5 class="modal-title fw-bold"><i class="fas fa-user-edit me-2"></i> تعديل بيانات المستخدم</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body p-4 bg-light">
                            <div class="mb-3">
                                <label class="form-label fw-bold text-dark">الاسم الكامل</label>
                                <input type="text" name="full_name" id="editName" class="form-control form-control-lg border-0 shadow-sm" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-bold text-dark">رقم الهاتف</label>
                                <input type="text" name="phone" id="editPhone" class="form-control form-control-lg border-0 shadow-sm" dir="ltr">
                            </div>
                        </div>
                        <div class="modal-footer bg-white border-0">
                            <button type="submit" class="btn btn-primary btn-lg w-100 fw-bold shadow-sm">حفظ التعديلات</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- سكريبت تشغيل النوافذ المنبثقة (تم حله هنا) -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function showIdModal(frontSrc, backSrc) {{
                document.getElementById('imgFront').src = frontSrc;
                document.getElementById('imgBack').src = backSrc;
                var myModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('idModal'));
                myModal.show();
            }}

            function editUser(id, name, phone) {{ 
                document.getElementById('editForm').action = '/dashboard/edit-user/' + id; 
                document.getElementById('editName').value = name; 
                document.getElementById('editPhone').value = phone; 
                var myModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editModal'));
                myModal.show(); 
            }}
        </script>
    </body>
    </html>
    """)


@dashboard_bp.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    """دالة الحذف النهائي للمستخدم من الداتا بيز"""
    if current_user.role != "Admin":
        return abort(403)
        
    user_to_delete = User.query.get_or_404(user_id)
    
    # حماية: لا يمكن للأدمن حذف نفسه
    if user_to_delete.id == current_user.id:
        flash("لا يمكنك حذف حسابك الإداري الخاص!", "error")
        return redirect(url_for('dashboard.users'))
        
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"تم حذف المستخدم ({user_to_delete.full_name}) نهائياً من النظام.", "success")
    except Exception as e:
        db.session.rollback()
        flash("لا يمكن حذف هذا المستخدم لأنه مرتبط بطلبات ومشاريع نشطة في المنصة.", "error")
        
    return redirect(url_for('dashboard.users'))


@dashboard_bp.route("/toggle-user/<int:user_id>", methods=["POST"])
@login_required
def toggle_user(user_id):
    if current_user.role != "Admin": return abort(403)
    u = User.query.get_or_404(user_id)
    u.is_active = not u.is_active
    db.session.commit()
    flash("تم تغيير حالة المستخدم", "success")
    return redirect(url_for('dashboard.users'))

@dashboard_bp.route("/edit-user/<int:user_id>", methods=["POST"])
@login_required
def edit_user(user_id):
    if current_user.role != "Admin": return abort(403)
    u = User.query.get_or_404(user_id)
    u.full_name = request.form.get("full_name")
    u.phone = request.form.get("phone")
    db.session.commit()
    flash("تم تحديث بيانات المستخدم", "success")
    return redirect(url_for('dashboard.users'))


@dashboard_bp.route("/analytics")
@login_required
def analytics():
    """صفحة التقارير والإحصائيات"""
    if current_user.role != "Admin":
        flash("هذه الصفحة مخصصة للمدراء فقط", "error")
        return redirect(url_for("dashboard.index"))

    try:
        # جمع الإحصائيات
        stats = {
            "total_users": User.query.count(),
            "total_startups": 0,
            "total_programs": Program.query.count(),
            "total_applications": 0,
        }

        # إنشاء صفحة التقارير بدون قوالب معقدة
        return f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>التقارير والإحصائيات</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }}
                .navbar {{ background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%); }}
                .stats-card {{ background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
                .chart-container {{ background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 2rem; height: auto; }}
                .chart-canvas {{ max-height: 400px !important; }}
                        
                    .logo{{
            width: 60px;
            margin-left: 10px;
            border-radius: 10px;
            }}
        
            </style>
        </head>
        <body>
            <nav class="navbar navbar-dark">
                <div class="container">
                    <a class="navbar-brand" href="/">
                        <img src="/static/nawatech.svg" class="logo">
                        نواتك
                    </a>
                    <div>
                        <a class="nav-link text-white d-inline" href="/dashboard/">
                            <i class="fas fa-arrow-right me-1"></i>العودة للوحة الإدارة
                        </a>
                        <a class="nav-link text-white d-inline ms-3" href="/logout">
                            <i class="fas fa-sign-out-alt me-1"></i>تسجيل الخروج
                        </a>
                    </div>
                </div>
            </nav>

            <div class="container mt-5">
                <div class="text-center mb-5">
                    <h1><i class="fas fa-chart-bar text-info me-2"></i>التقارير والإحصائيات</h1>
                    <p class="lead">تحليل شامل لأداء المنصة</p>
                </div>
                
                <!-- إحصائيات سريعة -->
                <div class="row mb-5">
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-users fa-3x text-primary mb-3"></i>
                            <h3>{stats['total_users']}</h3>
                            <p>إجمالي المستخدمين</p>
                            <small class="text-success">
                                <i class="fas fa-arrow-up me-1"></i>+12% هذا الشهر
                            </small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-building fa-3x text-success mb-3"></i>
                            <h3>{stats['total_startups']}</h3>
                            <p>الشركات الناشئة</p>
                            <small class="text-success">
                                <i class="fas fa-arrow-up me-1"></i>+8% هذا الشهر
                            </small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-graduation-cap fa-3x text-info mb-3"></i>
                            <h3>{stats['total_programs']}</h3>
                            <p>البرامج النشطة</p>
                            <small class="text-warning">
                                <i class="fas fa-minus me-1"></i>0% هذا الشهر
                            </small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card text-center">
                            <i class="fas fa-dollar-sign fa-3x text-warning mb-3"></i>
                            <h3>2.3M</h3>
                            <p>التمويل المقدم ($)</p>
                            <small class="text-success">
                                <i class="fas fa-arrow-up me-1"></i>+25% هذا الشهر
                            </small>
                        </div>
                    </div>
                </div>
                
                <!-- الرسوم البيانية -->
                <div class="row">
                    <div class="col-lg-8 mb-4">
                        <div class="chart-container">
                            <h5 class="mb-4">
                                <i class="fas fa-chart-line me-2"></i>
                                نمو المستخدمين والشركات
                            </h5>
                            <canvas id="growthChart" style="max-height: 400px !important; height: 400px;"></canvas>
                        </div>
                    </div>
                    
                    <div class="col-lg-4 mb-4">
                        <div class="chart-container">
                            <h5 class="mb-4">
                                <i class="fas fa-chart-pie me-2"></i>
                                توزيع المستخدمين
                            </h5>
                            <canvas id="userChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- التقرير المالي -->
                <div class="row">
                    <div class="col-12">
                        <div class="chart-container">
                            <h5 class="mb-4">
                                <i class="fas fa-dollar-sign me-2"></i>
                                التقرير المالي
                            </h5>
                            
                            <div class="row mb-4">
                                <div class="col-md-3 text-center">
                                    <div class="p-3 bg-success-subtle rounded">
                                        <h3 class="fw-bold text-success">$2.3M</h3>
                                        <p class="mb-0">إجمالي التمويل</p>
                                    </div>
                                </div>
                                <div class="col-md-3 text-center">
                                    <div class="p-3 bg-primary-subtle rounded">
                                        <h3 class="fw-bold text-primary">$85K</h3>
                                        <p class="mb-0">متوسط التمويل</p>
                                    </div>
                                </div>
                                <div class="col-md-3 text-center">
                                    <div class="p-3 bg-warning-subtle rounded">
                                        <h3 class="fw-bold text-warning">27</h3>
                                        <p class="mb-0">شركات ممولة</p>
                                    </div>
                                </div>
                                <div class="col-md-3 text-center">
                                    <div class="p-3 bg-info-subtle rounded">
                                        <h3 class="fw-bold text-info">73%</h3>
                                        <p class="mb-0">معدل النجاح</p>
                                    </div>
                                </div>
                            </div>
                            
                            <canvas id="financialChart" class="chart-canvas" style="max-height: 400px !important;"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- أزرار التصدير -->
                <div class="text-center mt-4">
                    <button class="btn btn-outline-primary me-2" onclick="exportPDF()">
                        <i class="fas fa-file-pdf me-2"></i>تصدير PDF
                    </button>
                    <button class="btn btn-outline-success me-2" onclick="exportExcel()">
                        <i class="fas fa-file-excel me-2"></i>تصدير Excel
                    </button>
                    <button class="btn btn-outline-info" onclick="exportCSV()">
                        <i class="fas fa-file-csv me-2"></i>تصدير CSV
                    </button>
                </div>
            </div>

            <script>
                // رسم بياني للنمو
                const growthCtx = document.getElementById('growthChart').getContext('2d');
                new Chart(growthCtx, {{
                    type: 'line',
                    data: {{
                        labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
                        datasets: [{{
                            label: 'المستخدمين',
                            data: [12, 19, 25, 32, 38, 47],
                            borderColor: '#1a237e',
                            backgroundColor: 'rgba(26, 35, 126, 0.1)',
                            tension: 0.2,
                            pointRadius: 6,
                            pointHoverRadius: 8,
                            borderWidth: 3
                        }}, {{
                            label: 'الشركات الناشئة',
                            data: [5, 8, 12, 18, 25, 35],
                            borderColor: '#f50057',
                            backgroundColor: 'rgba(245, 0, 87, 0.1)',
                            tension: 0.2,
                            pointRadius: 6,
                            pointHoverRadius: 8,
                            borderWidth: 3
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{
                            intersect: false,
                            mode: 'index'
                        }},
                        plugins: {{
                            legend: {{
                                position: 'top',
                                labels: {{
                                    usePointStyle: true,
                                    padding: 20
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                grid: {{
                                    display: true,
                                    color: 'rgba(0,0,0,0.1)'
                                }}
                            }},
                            y: {{
                                beginAtZero: true,
                                grid: {{
                                    display: true,
                                    color: 'rgba(0,0,0,0.1)'
                                }},
                                ticks: {{
                                    stepSize: 10
                                }}
                            }}
                        }},
                        elements: {{
                            point: {{
                                hoverBorderWidth: 3
                            }}
                        }}
                    }}
                }});

                // رسم بياني للمستخدمين
                const userCtx = document.getElementById('userChart').getContext('2d');
                new Chart(userCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['رواد أعمال', 'مستشارين', 'مدربين', 'مدراء'],
                        datasets: [{{
                            data: [35, 12, 8, 3],
                            backgroundColor: ['#1a237e', '#f50057', '#00e676', '#ff9800']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{
                                position: 'bottom'
                            }}
                        }}
                    }}
                }});

                // رسم بياني مالي
                const financialCtx = document.getElementById('financialChart').getContext('2d');
                new Chart(financialCtx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                        datasets: [{{
                            label: 'التمويل المقدم ($)',
                            data: [450000, 580000, 720000, 550000],
                            backgroundColor: '#4caf50'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    callback: function(value) {{
                                        return '$' + value.toLocaleString();
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});

                function exportPDF() {{
                    alert('تصدير التقرير بصيغة PDF 📊');
                }}

                function exportExcel() {{
                    alert('تصدير التقرير بصيغة Excel 📊');
                }}

                function exportCSV() {{
                    alert('تصدير التقرير بصيغة CSV 📊');
                }}
            </script>
        </body>
        </html>
        """

    except Exception as e:
        return f"""
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h1 style="color: red;">خطأ في تحميل التقارير</h1>
            <p>حدث خطأ: {str(e)}</p>
            <a href="/dashboard/" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">العودة للوحة الإدارة</a>
        </div>
        """


@dashboard_bp.route("/reports")
@login_required
def reports():
    """صفحة التقارير والإحصائيات"""
    if current_user.role != "Admin":
        flash("هذه الصفحة مخصصة للمدراء فقط", "error")
        return redirect(url_for("dashboard.index"))

    try:
        # Collect statistics for reports
        stats = {
            "total_users": User.query.count(),
            "total_startups": Startup.query.count() if Startup.query.first() else 0,
            "total_programs": Program.query.count(),
            "total_applications": (
                Application.query.count() if Application.query.first() else 0
            ),
        }

        return render_template("dashboard/reports.html", stats=stats)
    except Exception as e:
        flash("حدث خطأ في تحميل التقارير", "error")
        return redirect(url_for("dashboard.index"))
        flash("حدث خطأ في تحميل التقارير", "error")
        return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/applications")
@login_required
def applications():
    if current_user.role != "Admin": return abort(403)

    apps = Application.query.order_by(Application.created_at.desc()).all()
    apps_html = ""
    for app in apps:
        status_bg = "success" if app.status == 'accepted' else "danger" if app.status == 'rejected' else "warning text-dark"
        score = app.startup.evaluation.total_score if app.startup.evaluation else 0
        
        apps_html += f"""
        <tr>
            <td class="fw-bold text-primary">{app.startup.name} <br><small class="text-muted">{app.startup.owner.full_name}</small></td>
            <td><span class="badge bg-secondary">{app.program.name}</span></td>
            <td>{app.startup.city}</td>
            <td><span class="badge bg-dark">{score}%</span></td>
            <td><span class="badge bg-{status_bg}">{app.status}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-dark fw-bold" onclick="alert('ملخص الفكرة: \\n {app.startup.summary}')">
                    <i class="fas fa-eye me-1"></i> التفاصيل
                </button>
            </td>
        </tr>
        """

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl"><head><title>رؤية الأفكار</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css" rel="stylesheet"><link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"></head>
    <body style="background:#f8f9fa;">
        <div class="container mt-5">
            <div class="d-flex justify-content-between mb-4">
                <h2 class="fw-bold"><i class="fas fa-lightbulb text-warning"></i> بنك الأفكار والمشاريع</h2>
                <a href="/dashboard" class="btn btn-outline-dark fw-bold">العودة للوحة</a>
            </div>
            <div class="card border-0 shadow-sm"><div class="card-body p-0">
                <table class="table table-hover align-middle mb-0"><thead class="bg-dark text-white"><tr><th>المشروع / الرائد</th><th>البرنامج</th><th>المدينة</th><th>تقييم AI</th><th>الحالة</th><th>عرض</th></tr></thead><tbody>{apps_html}</tbody></table>
            </div></div>
        </div>
    </body></html>
    """)


from models import Service

@dashboard_bp.route("/services-management", methods=["GET", "POST"])
@login_required
def services_management():
    if current_user.role != "Admin":
        return abort(403)

    # إضافة خدمة جديدة
    if request.method == "POST" and 'add_new' in request.form:
        new_service = Service(
            title=request.form.get('new_title'),
            description=request.form.get('new_description'),
            price=request.form.get('new_price'),
            button_text=request.form.get('new_button_text'),
            icon=request.form.get('new_icon', 'fas fa-star')
        )
        db.session.add(new_service)
        db.session.commit()
        flash("✅ تمت إضافة الباقة الجديدة بنجاح", "success")
        return redirect(url_for('dashboard.services_management'))

    # تعديل خدمة موجودة
    if request.method == "POST" and 'service_id' in request.form:
        service = Service.query.get_or_404(request.form.get('service_id'))
        service.title = request.form.get('title')
        service.description = request.form.get('description')
        service.price = request.form.get('price')
        service.button_text = request.form.get('button_text')
        new_currency = request.form.get('currency')
        if new_currency in ['MYR', 'USD']:
            service.currency = new_currency
            service.currency_symbol = 'رنجت' if new_currency == 'MYR' else 'دولار'
            
        db.session.commit()
        flash("✅ تم تحديث الخدمة بنجاح", "success")
        return redirect(url_for('dashboard.services_management'))

    services = Service.query.all()
    return render_template('dashboard/services_management.html', services=services)

from models import ServicePurchase
@dashboard_bp.route("/purchases")
@login_required
def purchases():
    if current_user.role != "Admin":
        return abort(403)

    purchases = ServicePurchase.query.order_by(ServicePurchase.created_at.desc()).all()
    
    return render_template('dashboard/purchases.html', purchases=purchases)
@dashboard_bp.route("/programs-management", methods=["GET", "POST"])
@login_required
def programs_management():
    if current_user.role != "Admin": return abort(403)

    if request.method == "POST":
        # إنشاء برنامج جديد
        p = Program(
            name=request.form.get('name'),
            type=request.form.get('type'),
            city=request.form.get('city'),
            cohort_code=request.form.get('cohort_code'),
            status=request.form.get('status'),
            description=request.form.get('description')
        )
        db.session.add(p)
        db.session.commit()
        flash("تم إضافة البرنامج بنجاح!", "success")
        return redirect(url_for('dashboard.programs_management'))

    progs = Program.query.all()
    progs_html = ""
    for p in progs:
        status_bg = "success" if p.status == 'open' else "danger"
        progs_html += f"""
        <tr>
            <td class="fw-bold text-primary">{p.name} <br><small class="text-muted">{p.cohort_code}</small></td>
            <td>{p.type}</td>
            <td>{p.city}</td>
            <td><span class="badge bg-{status_bg}">{p.status}</span></td>
            <td>
                <form action="/dashboard/delete-program/{p.id}" method="POST" style="display:inline;" onsubmit="return confirm('تأكيد الحذف نهائياً؟')">
                    <button class="btn btn-sm btn-danger fw-bold"><i class="fas fa-trash"></i> حذف</button>
                </form>
            </td>
        </tr>
        """

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl"><head><title>إدارة البرامج</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css" rel="stylesheet"><link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"></head>
    <body style="background:#f8f9fa;">
        <div class="container mt-5 mb-5">
            <div class="d-flex justify-content-between mb-4">
                <h2 class="fw-bold"><i class="fas fa-graduation-cap text-success"></i> إدارة البرامج</h2>
                <a href="/dashboard" class="btn btn-outline-dark fw-bold">العودة للوحة</a>
            </div>
            
            <div class="row"><div class="col-md-4">
                <div class="card shadow-sm border-0 mb-4"><div class="card-header bg-primary text-white"><h5 class="mb-0">إضافة برنامج</h5></div>
                <div class="card-body"><form method="POST">
                    <input type="text" name="name" class="form-control mb-2" placeholder="اسم البرنامج" required>
                    <select name="type" class="form-select mb-2"><option value="incubator">حاضنة</option><option value="accelerator">مسرعة</option></select>
                    <input type="text" name="city" class="form-control mb-2" placeholder="المدينة (مثال: بغداد)">
                    <input type="text" name="cohort_code" class="form-control mb-2" placeholder="الرمز (مثال: B1)">
                    <select name="status" class="form-select mb-2"><option value="open">مفتوح للتقديم</option><option value="closed">مغلق</option></select>
                    <textarea name="description" class="form-control mb-3" placeholder="وصف البرنامج..."></textarea>
                    <button type="submit" class="btn btn-primary w-100 fw-bold">حفظ البرنامج</button>
                </form></div></div>
            </div>
            <div class="col-md-8"><div class="card shadow-sm border-0"><div class="card-body p-0">
                <table class="table table-hover align-middle mb-0"><thead class="bg-dark text-white"><tr><th>البرنامج</th><th>النوع</th><th>المدينة</th><th>الحالة</th><th>حذف</th></tr></thead><tbody>{progs_html}</tbody></table>
            </div></div></div></div>
        </div>
    </body></html>
    """)

@dashboard_bp.route("/delete-program/<int:p_id>", methods=["POST"])
@login_required
def delete_program(p_id):
    if current_user.role != "Admin": return abort(403)
    p = Program.query.get_or_404(p_id)
    db.session.delete(p)
    db.session.commit()
    flash("تم حذف البرنامج", "success")
    return redirect(url_for('dashboard.programs_management'))


@dashboard_bp.route("/startups-management")
@login_required
def startups_management():
    """إدارة الشركات الناشئة"""
    if current_user.role != "Admin":
        flash("هذه الصفحة مخصصة للمدراء فقط", "error")
        return redirect(url_for("dashboard.index"))

    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>إدارة الشركات الناشئة</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
                    .logo{{
            width: 60px;
            margin-left: 10px;
            border-radius: 10px;
            }}
        </style>
    </head>
    <body style="background: #f8f9fa;">
        <nav class="navbar navbar-dark" style="background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);">
            <div class="container">
                <a class="navbar-brand" href="/">
                <img src="/static/nawatech.svg" class="logo">
                نواتك 
                </a>
                <a class="nav-link text-white" href="/dashboard/"><i class="fas fa-arrow-right me-1"></i>العودة</a>
            </div>
        </nav>
        
        <div class="container mt-5">
            <h1><i class="fas fa-building text-info me-2"></i>إدارة الشركات الناشئة</h1>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>0</h3>
                            <p>شركات مسجلة</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>0</h3>
                            <p>شركات نشطة</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>$0</h3>
                            <p>إجمالي التمويل</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mt-4">
                <div class="card-body text-center py-5">
                    <i class="fas fa-building fa-3x text-muted mb-3"></i>
                    <h5>لا توجد شركات ناشئة مسجلة حالياً</h5>
                    <p class="text-muted">سيتم عرض الشركات هنا عند تسجيلها</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@dashboard_bp.route("/mentors-management")
@login_required
def mentors_management():
    """إدارة المرشدين والمستشارين"""
    if current_user.role != "Admin":
        flash("هذه الصفحة مخصصة للمدراء فقط", "error")
        return redirect(url_for("dashboard.index"))

    try:
        mentors = User.query.filter(User.role.in_(["Advisor", "Trainer"])).all()

        mentors_html = ""
        for mentor in mentors:
            role_info = {
                "Advisor": {"badge": "success", "text": "مستشار", "icon": "user-tie"},
                "Trainer": {
                    "badge": "info",
                    "text": "مدرب",
                    "icon": "chalkboard-teacher",
                },
            }.get(
                mentor.role, {"badge": "secondary", "text": "غير محدد", "icon": "user"}
            )

            mentors_html += f"""
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="avatar bg-{role_info['badge']} text-white me-3" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                            {mentor.full_name[0] if mentor.full_name else 'U'}
                        </div>
                        <div>
                            <div class="fw-bold">{mentor.full_name}</div>
                            <small class="text-muted">{mentor.email}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge bg-{role_info['badge']}">
                        <i class="fas fa-{role_info['icon']} me-1"></i>
                        {role_info['text']}
                    </span>
                </td>
                <td>{'نشط' if mentor.is_active else 'غير نشط'}</td>
                <td>0</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="viewMentor({mentor.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="assignMentor({mentor.id})">
                            <i class="fas fa-link"></i>
                        </button>
                        <button class="btn btn-outline-warning" onclick="editMentor({mentor.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>إدارة المرشدين</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

            <style>
            .logo{{
            width: 60px;
            margin-left: 10px;
            border-radius: 10px;
            }}
            </style>
        </head>
        <body style="background: #f8f9fa;">
            <nav class="navbar navbar-dark" style="background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);">
                <div class="container">
                    <a class="navbar-brand" href="/">
                    <img src="/static/nawatech.svg" class="logo">
                    نواتك
                    </a>
                    <a class="nav-link text-white" href="/dashboard/"><i class="fas fa-arrow-right me-1"></i>العودة</a>
                </div>
            </nav>
            
            <div class="container mt-5">
                <h1><i class="fas fa-user-tie text-purple me-2" style="color: #6f42c1;"></i>إدارة المرشدين</h1>
                
                <div class="row mt-4 mb-4">
                    <div class="col-md-4">
                        <div class="card text-center">
                            <div class="card-body">
                                <h4 class="text-success">{User.query.filter_by(role='Advisor').count()}</h4>
                                <p>المستشارين</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center">
                            <div class="card-body">
                                <h4 class="text-info">{User.query.filter_by(role='Trainer').count()}</h4>
                                <p>المدربين</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-center">
                            <div class="card-body">
                                <h4 class="text-warning">0</h4>
                                <p>جلسات نشطة</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">قائمة المرشدين</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>المرشد</th>
                                        <th>الدور</th>
                                        <th>الحالة</th>
                                        <th>عدد الجلسات</th>
                                        <th>الإجراءات</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {mentors_html}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                function viewMentor(id) {{ alert('عرض المرشد رقم ' + id); }}
                function assignMentor(id) {{ alert('تعيين المرشد رقم ' + id); }}
                function editMentor(id) {{ alert('تعديل المرشد رقم ' + id); }}
            </script>
        </body>
        </html>
        """

    except Exception as e:
        return f"<h1>خطأ: {str(e)}</h1><a href='/dashboard/'>العودة</a>"


# ==================================
# NEW ROUTES FOR VERIFICATION SYSTEM
# ==================================


@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """صفحة توثيق الحساب (هوية للرائد/مدرب/مستشار - سجل تجاري للممول)"""
    
    if request.method == "POST":
        upload_path = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(os.path.join(upload_path, 'ids'), exist_ok=True)
        
        # 1. إذا كان ممول (يرفع سجل تجاري)
        if current_user.role == 'Investor':
            if "commercial_register" not in request.files:
                flash("الرجاء إرفاق ملف السجل التجاري", "error")
                return redirect(request.url)
                
            cr_file = request.files["commercial_register"]
            if cr_file and cr_file.filename:
                # استخدام / بدلاً من \ لتجنب مشاكل مسارات الويندوز
                cr_filename = secure_filename(f"cr_{current_user.id}_{cr_file.filename}")
                cr_file.save(os.path.join(upload_path, 'ids', cr_filename))
                current_user.commercial_register_path = f"uploads/ids/{cr_filename}"
                current_user.verification_status = "pending"
                db.session.commit()
                flash("تم رفع السجل التجاري بنجاح وهو الآن قيد المراجعة الإدارية", "success")
                return redirect(url_for("dashboard.settings"))
                
        # 2. إذا كان (رائد أو مدرب أو مستشار) - يرفع الهوية الوطنية
        else:
            if "id_front" not in request.files or "id_back" not in request.files:
                flash("الرجاء إرفاق صورتي الهوية معاً", "error")
                return redirect(request.url)

            id_front_file = request.files["id_front"]
            id_back_file = request.files["id_back"]

            if id_front_file.filename and id_back_file.filename:
                front_filename = secure_filename(f"user_{current_user.id}_front_{id_front_file.filename}")
                back_filename = secure_filename(f"user_{current_user.id}_back_{id_back_file.filename}")

                id_front_file.save(os.path.join(upload_path, 'ids', front_filename))
                id_back_file.save(os.path.join(upload_path, 'ids', back_filename))

                # حفظ المسار بصيغة تعمل على كل الأنظمة
                current_user.id_front_path = f"uploads/ids/{front_filename}"
                current_user.id_back_path = f"uploads/ids/{back_filename}"
                
                current_user.verification_status = "pending"
                db.session.commit()
                flash("تم رفع مستندات الهوية بنجاح وهي الآن قيد المراجعة الإدارية", "success")
                return redirect(url_for("dashboard.settings"))

    # تحضير رسائل الحالة
    status_map = {
        "unverified": ("لم يتم التوثيق بعد", "secondary"),
        "pending": ("التوثيق قيد المراجعة", "info"),
        "verified": ("الحساب موثق", "success"),
        "rejected": ("تم رفض التوثيق، يرجى الرفع مرة أخرى", "danger"),
    }
    status_text, status_color = status_map.get(current_user.verification_status, ("", ""))

    # تصميم صفحة الإعدادات المدمجة
    return render_template_string("""
    {% extends "base.html" %}
    {% block title %}إعدادات الحساب والتوثيق{% endblock %}
    {% block content %}
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-lg-8 col-md-10">
                <div class="card shadow-sm border-0">
                    <div class="card-header bg-dark text-black py-3">
                        <h4 class="mb-0"><i class="fas fa-shield-alt text-warning me-2"></i> توثيق الحساب الرسمي</h4>
                    </div>
                    <div class="card-body p-5 bg-light">
                        <div class="text-center mb-4">
                            <h5 class="text-dark fw-bold">حالة الحساب: <span class="badge fs-5 bg-{{ status_color }}">{{ status_text }}</span></h5>
                        </div>
                        <hr>

                        {% if current_user.verification_status in ['unverified', 'rejected'] %}
                            
                            <!-- فورم المستثمر -->
                            {% if current_user.role == 'Investor' %}
                            <div class="alert alert-warning border-warning">
                                <p class="mb-2 fw-bold text-dark"><i class="fas fa-info-circle me-2"></i> للوصول إلى قاعدة بيانات المشاريع، يرجى رفع السجل التجاري (أو البطاقة الضريبية) لشركتك أو صفتك الاعتبارية.</p>
                            </div>
                            <form method="POST" enctype="multipart/form-data" class="mt-4 bg-white p-4 rounded shadow-sm border">
                                <div class="mb-4">
                                    <label class="form-label fw-bold text-dark fs-5"><i class="fas fa-file-pdf text-danger me-2"></i> السجل التجاري (PDF أو صورة) *</label>
                                    <input class="form-control form-control-lg" type="file" name="commercial_register" accept=".pdf, image/png, image/jpeg" required>
                                </div>
                                <button type="submit" class="btn btn-warning btn-lg w-100 fw-bold text-dark shadow"><i class="fas fa-upload me-2"></i> إرسال السجل للمراجعة الإدارية</button>
                            </form>

                            <!-- فورم الرائد/المدرب/المستشار -->
                            {% else %}
                            <div class="alert alert-info border-info">
                                <p class="mb-2 fw-bold text-dark"><i class="fas fa-info-circle me-2"></i> يرجى رفع صورة واضحة للوجه الأمامي والخلفي لبطاقة الهوية الوطنية.</p>
                            </div>
                            <form method="POST" enctype="multipart/form-data" class="mt-4 bg-white p-4 rounded shadow-sm border">
                                <div class="mb-3">
                                    <label class="form-label fw-bold text-dark">الوجه الأمامي لبطاقة الهوية *</label>
                                    <input class="form-control" type="file" name="id_front" accept="image/*" required>
                                </div>
                                <div class="mb-4">
                                    <label class="form-label fw-bold text-dark">الوجه الخلفي لبطاقة الهوية *</label>
                                    <input class="form-control" type="file" name="id_back" accept="image/*" required>
                                </div>
                                <button type="submit" class="btn btn-primary btn-lg w-100 fw-bold shadow"><i class="fas fa-upload me-2"></i> رفع الهوية وطلب المراجعة</button>
                            </form>
                            {% endif %}

                        {% elif current_user.verification_status == 'pending' %}
                        <div class="text-center py-4">
                            <i class="fas fa-clock fa-4x text-info mb-3"></i>
                            <h4 class="fw-bold text-dark">المستندات قيد المراجعة</h4>
                            <p class="text-muted fs-5">لقد قمنا باستلام مستنداتك بنجاح، فريق الإدارة يقوم بمراجعتها حالياً.</p>
                        </div>
                        
                        {% elif current_user.verification_status == 'verified' %}
                        <div class="text-center py-4">
                            <i class="fas fa-check-circle fa-4x text-success mb-3"></i>
                            <h4 class="fw-bold text-dark">حسابك موثق بالكامل</h4>
                            {% if current_user.role == 'Investor' %}
                                <p class="text-muted fs-5 mb-4">يمكنك الآن استعراض المشاريع الجاهزة للتمويل.</p>
                                <a href="/investor/portal" class="btn btn-success btn-lg fw-bold px-5">الدخول لبوابة التمويل</a>
                            {% else %}
                                <p class="text-muted fs-5">يمكنك الآن الوصول لجميع الميزات في لوحتك.</p>
                            {% endif %}
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """, status_text=status_text, status_color=status_color)

@dashboard_bp.route("/approve-verification/<int:user_id>")
@login_required
def approve_verification(user_id):
    if current_user.role != "Admin":
        flash("غير مصرح لك بالقيام بهذا الإجراء", "error")
        return redirect(url_for("dashboard.index"))

    user_to_verify = User.query.get_or_404(user_id)
    user_to_verify.verification_status = "verified"
    db.session.commit()
    flash(f"تم توثيق حساب المستخدم {user_to_verify.full_name} بنجاح.", "success")
    return redirect(url_for("dashboard.users"))


@dashboard_bp.route("/reject-verification/<int:user_id>")
@login_required
def reject_verification(user_id):
    if current_user.role != "Admin":
        flash("غير مصرح لك بالقيام بهذا الإجراء", "error")
        return redirect(url_for("dashboard.index"))

    user_to_reject = User.query.get_or_404(user_id)
    user_to_reject.verification_status = "rejected"
    db.session.commit()
    flash(f"تم رفض طلب توثيق المستخدم {user_to_reject.full_name}.", "warning")
    return redirect(url_for("dashboard.users"))


import os
from flask import send_from_directory, current_app, abort

@dashboard_bp.route("/view-id-image/<int:user_id>/<side>")
@login_required
def view_id_image(user_id, side):
    """دالة نهائية لقراءة صور الهوية بأمان تام"""
    if current_user.role != "Admin":
        abort(403)

    user = User.query.get_or_404(user_id)
    path = user.id_front_path if side == "front" else user.id_back_path
    
    if not path:
        return "لا يوجد مسار للصورة في قاعدة البيانات", 404

    # استخراج اسم الملف الصافي (مثل: user_5_front.jpg)
    filename = os.path.basename(path.replace('\\', '/'))
    
    # تحديد المسارات المحتملة
    # 1. المسار الرسمي للإعدادات
    dir1 = os.path.join(current_app.config.get("UPLOAD_FOLDER", ""), 'ids')
    # 2. المسار الثابت داخل مجلد static
    dir2 = os.path.join(current_app.root_path, 'static', 'uploads', 'ids')
    
    # الفحص وإرسال الصورة
    if os.path.exists(os.path.join(dir1, filename)):
        return send_from_directory(dir1, filename)
    elif os.path.exists(os.path.join(dir2, filename)):
        return send_from_directory(dir2, filename)
    else:
        return "الملف غير موجود فعلياً في السيرفر", 404
@dashboard_bp.route("/library")
@login_required
def library():
    """المكتبة الرقمية (تظهر فقط للمقبولين)"""
    # التأكد من أنه مقبول في برنامج واحد على الأقل
    accepted_apps = Application.query.join(Startup).filter(Startup.owner_user_id == current_user.id, Application.status == 'accepted').count()
    if accepted_apps == 0:
        flash("المكتبة متاحة فقط للرواد المقبولين في البرامج التدريبية.", "warning")
        return redirect(url_for('dashboard.index'))
    return render_template("dashboard/library.html")
from models import FormOneSubmission, MentoringSession
import uuid # لإنشاء أسماء غرف اجتماعات سرية
@dashboard_bp.route("/api/submit-form-one", methods=['POST'])
@login_required
def submit_form_one():
    data = request.get_json()
    app_id = data.get('app_id')
    customer_needs = data.get('customer_needs')
    ultimate_goal = data.get('ultimate_goal')

    existing = FormOneSubmission.query.filter_by(application_id=app_id).first()
    if not existing:
        form = FormOneSubmission(application_id=app_id, customer_needs=customer_needs, ultimate_goal=ultimate_goal)
        db.session.add(form)
        
        # تفعيل التنبيه للمدرب
        app = Application.query.get(app_id)
        if app:
            app.form_one_submitted = True
            app.form_one_viewed = False # إعادة التنبيه ليراه المدرب
            
        db.session.commit()
    return jsonify({"status": "success"})
@dashboard_bp.route("/mentoring/<int:app_id>")
@login_required
def mentoring(app_id):
    app = Application.query.get_or_404(app_id)
    if app.startup.owner_user_id != current_user.id or app.status != 'accepted':
        return redirect(url_for('dashboard.index'))
        
    meetings = MentoringSession.query.filter_by(application_id=app_id).order_by(MentoringSession.created_at.desc()).all()
    return render_template("dashboard/mentoring.html", app=app, meetings=meetings)

@dashboard_bp.route("/request-meeting/<int:app_id>", methods=['POST'])
@login_required
def request_meeting(app_id):
    app = Application.query.get_or_404(app_id)
    date = request.form.get('date')
    time = request.form.get('time')
    
    # اسم غرفة فريد للاجتماع
    room_name = f"Nawatech_{app.id}_{uuid.uuid4().hex[:8]}"
    
    meeting = MentoringSession(
        application_id=app.id,
        trainer_id=app.trainer_id,
        requested_date=date,
        requested_time=time,
        room_name=room_name
    )
    db.session.add(meeting)
    db.session.commit()
    flash("تم إرسال طلب الاجتماع لمدربك. ستتلقى الرد قريباً.", "success")
    return redirect(url_for('dashboard.mentoring', app_id=app.id))

@dashboard_bp.route("/live-room/<room_name>")
@login_required
def live_room(room_name):
    """صفحة الاجتماع المباشر (تفتح الكاميرا والمايك باستخدام Jitsi)"""
    return render_template("dashboard/live_room.html", room_name=room_name, user_name=current_user.full_name)

@dashboard_bp.route("/startup/<int:startup_id>/edit", methods=["GET", "POST"])
@login_required
def startup_edit(startup_id):
    """دالة التعديل للشركة/الفكرة (لإصلاح خطأ BuildError)"""
    startup = Startup.query.get_or_404(startup_id)
    if startup.owner_user_id != current_user.id:
        flash("غير مصرح لك بتعديل هذه الفكرة", "error")
        return redirect(url_for("dashboard.index"))
    
    if request.method == "POST":
        startup.name = request.form.get("name", startup.name)
        startup.summary = request.form.get("summary", startup.summary)
        db.session.commit()
        flash("تم الحفظ بنجاح", "success")
        return redirect(url_for("dashboard.startup_detail", startup_id=startup.id))
        
    return render_template("dashboard/startup_edit.html", startup=startup)
@dashboard_bp.route("/submit-final-project/<int:app_id>", methods=['POST'])
@login_required
def submit_final_project(app_id):
    """استلام مشروع التخرج من الرائد (ملف أو نص)"""
    app = Application.query.get_or_404(app_id)
    
    # إذا رفع ملف
    if 'project_file' in request.files:
        file = request.files['project_file']
        if file and file.filename:
            save_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'projects')
            os.makedirs(save_dir, exist_ok=True)
            filename = secure_filename(f"proj_{app.id}_{file.filename}")
            file.save(os.path.join(save_dir, filename))
            app.final_project_file = f"uploads/projects/{filename}"
            
    # إذا كتب في المحرر الرقمي
    digital_text = request.form.get('digital_editor_text')
    if digital_text:
        app.final_project_text = digital_text

    app.final_project_submitted = True
    app.project_viewed = False
    db.session.commit()
    
    flash("تم إرسال مشروع التخرج للمدرب بنجاح! راقب هذه الصفحة لترى ملاحظاته.", "success")
    return redirect(url_for('dashboard.learning_hub', app_id=app.id))