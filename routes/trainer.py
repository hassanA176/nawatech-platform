import os
import json
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import MentoringSession, FormOneSubmission

# رجعنا للمكتبة التي تعمل عندك بنجاح لتفادي مشاكل السيرفر
import google.generativeai as genai
from models import LessonProgress, MentoringSession, FormOneSubmission
from models import db, User, Startup, Application, Program, TrainerCourse, CourseLesson, StartupEvaluation

trainer_bp = Blueprint('trainer', __name__, url_prefix='/trainer')

# إعداد مفتاح جيمناي
GENAI_API_KEY = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GENAI_API_KEY) if GENAI_API_KEY else None

@trainer_bp.before_request
def require_trainer_and_verification():
    if not current_user.is_authenticated or current_user.role != 'Trainer':
        flash('يجب أن تكون مدرباً للوصول لهذه الصفحة', 'error')
        return redirect(url_for('auth.login'))
    if current_user.verification_status != 'verified' and request.endpoint != 'dashboard.settings':
        flash('يجب أن يتم توثيق حسابك من قبل الإدارة أولاً.', 'warning')
        return redirect(url_for('dashboard.settings'))

from models import LessonProgress # أضف هذا في أعلى الملف مع باقي الاستيرادات

from models import AdvisorMessage # أضف هذا في أعلى الملف

@trainer_bp.route('/')
@trainer_bp.route('/dashboard')
@login_required
def dashboard():
    my_startups = Application.query.filter_by(trainer_id=current_user.id, status='accepted').all()
    my_courses_count = TrainerCourse.query.filter_by(trainer_id=current_user.id).count()
    pending_meetings = MentoringSession.query.filter_by(trainer_id=current_user.id, status='pending').all()
    
    # === جلب رسائل/طلبات المستشارين الموجهة لهذا المدرب ===
    advisor_requests = AdvisorMessage.query.filter_by(trainer_id=current_user.id).order_by(AdvisorMessage.created_at.desc()).all()
    
    for app in my_startups:
        total_prep_lessons = 3
        trainer_courses = TrainerCourse.query.filter_by(trainer_id=current_user.id, program_id=app.program_id).all()
        trainer_lessons_count = sum([len(c.lessons) for c in trainer_courses])
        total_lessons = total_prep_lessons + trainer_lessons_count
        completed_count = LessonProgress.query.filter_by(application_id=app.id).count()
        app.progress_percent = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0
        app.has_form_one = FormOneSubmission.query.filter_by(application_id=app.id).first()
            
    stats = {'my_startups_count': len(my_startups), 'my_courses_count': my_courses_count, 'pending_meetings_count': len(pending_meetings)}
    advisors = User.query.filter_by(role='Advisor', verification_status='verified').all()
    
    return render_template('trainer/dashboard.html', stats=stats, my_startups=my_startups, pending_meetings=pending_meetings, advisor_requests=advisor_requests,advisors=advisors)

from models import SharedProject, FundingMessage # استيراد الجداول
from models import AdvisorMessage, FundingMessage # تأكد من استيراد الجداول

@trainer_bp.route('/dismiss-advisor-message/<int:msg_id>', methods=['POST'])
@login_required
def dismiss_advisor_message(msg_id):
    """دالة لإغلاق/حذف رسالة المستشار عندما يضغط المدرب على زر X"""
    msg = AdvisorMessage.query.get_or_404(msg_id)
    if msg.trainer_id == current_user.id:
        db.session.delete(msg)
        db.session.commit()
    return redirect(url_for('trainer.dashboard'))

@trainer_bp.route('/share-projects', methods=['POST'])
@login_required
def share_projects():
    """إرسال المشاريع المحددة للمستشار"""
    advisor_id = request.form.get('advisor_id')
    selected_apps = request.form.getlist('app_ids') # جلب الـ Checkboxes
    
    if not selected_apps:
        flash("الرجاء تحديد مشروع واحد على الأقل", "warning")
        return redirect(url_for('trainer.dashboard'))
        
    for app_id in selected_apps:
        # التأكد من عدم إرساله مسبقاً لنفس المستشار
        if not SharedProject.query.filter_by(advisor_id=advisor_id, application_id=app_id).first():
            share = SharedProject(trainer_id=current_user.id, advisor_id=advisor_id, application_id=app_id)
            db.session.add(share)
            
    db.session.commit()
    flash("تم إرسال المشاريع المحددة للمستشار بنجاح!", "success")
    return redirect(url_for('trainer.dashboard'))

@trainer_bp.route('/funding-inbox')
@login_required
def funding_inbox():
    """صندوق وارد المدرب لرسائل الممولين"""
    messages = FundingMessage.query.filter_by(trainer_id=current_user.id).order_by(FundingMessage.created_at.desc()).all()
    return render_template('trainer/funding_inbox.html', messages=messages)
@trainer_bp.route('/manage-meetings', methods=['GET', 'POST'])
@login_required
def manage_meetings():
    """شاشة المدرب لقبول أو تأجيل اجتماعات الفيديو"""
    if request.method == 'POST':
        meeting_id = request.form.get('meeting_id')
        action = request.form.get('action')
        meeting = MentoringSession.query.get(meeting_id)
        
        if action == 'approve':
            meeting.status = 'approved'
            flash("تمت الموافقة على الموعد وسيتم إرسال الرابط للرائد.", "success")
        elif action == 'reschedule':
            meeting.requested_date = request.form.get('new_date')
            meeting.requested_time = request.form.get('new_time')
            meeting.status = 'approved'
            flash("تم تغيير الموعد والموافقة عليه.", "info")
            
        db.session.commit()
        return redirect(url_for('trainer.manage_meetings'))
        
    meetings = MentoringSession.query.filter_by(trainer_id=current_user.id).order_by(MentoringSession.created_at.desc()).all()
    return render_template('trainer/meetings.html', meetings=meetings)

from models import FormOneSubmission # تأكد من وجود هذا الاستيراد في أعلى الملف

@trainer_bp.route('/review-project/<int:app_id>', methods=['GET', 'POST'])
@login_required
def review_project(app_id):
    """صفحة استعراض مشروع التخرج والاستمارة 1"""
    app = Application.query.get_or_404(app_id)
    
    # === جلب الاستمارة بشكل مباشر ومضمون 100% ===
    form_one = FormOneSubmission.query.filter_by(application_id=app.id).first()
    
    # إخفاء التنبيهات لأن المدرب دخل للصفحة وشاهدها
    if app.form_one_submitted:
        app.form_one_viewed = True
    if app.final_project_submitted:
        app.project_viewed = True
    db.session.commit()
    
    if request.method == 'POST':
        feedback = request.form.get('feedback')
        if feedback:
            app.trainer_feedback = feedback
            db.session.commit()
            flash('تم إرسال الملاحظات للرائد بنجاح!', 'success')
            
        if 'send_to_advisor' in request.form:
            app.forwarded_to_advisor = True
            db.session.commit()
            flash('تم تحويل المشروع للمستشار!', 'info')
            
        return redirect(url_for('trainer.dashboard'))

    # إرسال form_one مباشرة للقالب
    return render_template('trainer/review_project.html', app=app, form_one=form_one)

# ==========================================
# نظام الأفكار وتحليل المخاطر
# ==========================================
@trainer_bp.route('/ideas-pool')
@login_required
def ideas_pool():
    """عرض الأفكار الجديدة (مع حل مشكلة تطابق لغة المدن)"""
    
    # قاموس لترجمة المدن لضمان التطابق بين التسجيل والتقديم
    city_map = {
        "بغداد": ["بغداد", "Baghdad"],
        "أربيل":["أربيل", "Erbil"],
        "البصرة": ["البصرة", "Basra"],
        "النجف": ["النجف", "Najaf"],
    }
    
    # تحديد المدن المسموح للمدرب رؤيتها بناءً على مدينته
    allowed_cities = city_map.get(current_user.city, [current_user.city])
    
    # جلب الأفكار التي في نفس مدينة المدرب فقط
    pending_applications = Application.query.join(Startup).filter(
        Application.status == 'submitted',
        Startup.city.in_(allowed_cities)
    ).order_by(Application.created_at.desc()).all()
    
    return render_template('trainer/ideas_pool.html', applications=pending_applications)
@trainer_bp.route('/grant-certificate/<int:app_id>', methods=['POST'])
@login_required
def grant_certificate(app_id):
    """دالة يقوم بها المدرب لمنح الشهادة للرائد بعد إتمام مشروعه"""
    app = Application.query.get_or_404(app_id)
    if app.trainer_id == current_user.id:
        app.is_graduated = True
        db.session.commit()
        flash('تم منح الشهادة وتخريج الرائد بنجاح!', 'success')
    return redirect(url_for('trainer.dashboard'))

@trainer_bp.route('/idea-details/<int:app_id>')
@login_required
def idea_details(app_id):
    application = Application.query.get_or_404(app_id)
    evaluation = application.startup.evaluation

    if evaluation and not evaluation.risk_matrix:
        prompt = f"""
        بصفتك خبير استراتيجي في إدارة المخاطر، قم بإنشاء "مصفوفة تحليل مخاطر" (Risk Analysis Matrix) لهذه الشركة الناشئة.
        اسم الشركة: {application.startup.name}
        القطاع: {application.startup.sector}
        المشكلة: {application.startup.problem}
        الحل: {application.startup.solution}
        السوق: {application.startup.target_market}

        المطلوب: قم بكتابة الرد بصيغة كود HTML مباشرة فقط (جدول أنيق باستخدام كلاسات Bootstrap 5 مثل table, table-bordered, table-hover). 
        الجدول يجب أن يحتوي على الأعمدة التالية: (نوع الخطر، وصف الخطر، مستوى التأثير (عالي/متوسط/منخفض)، احتمالية الحدوث، استراتيجية التخفيف).
        لا تكتب أي نصوص خارج وسم <table>.
        """
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            response = model.generate_content(prompt)
            html_content = response.text.replace('```html', '').replace('```', '').strip()
            evaluation.risk_matrix = html_content
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"AI Risk Matrix Error: {e}")
            evaluation.risk_matrix = "<div class='alert alert-warning'>تعذر توليد مصفوفة المخاطر حالياً.</div>"
            db.session.commit()

    return render_template('trainer/idea_details.html', app=application)

@trainer_bp.route('/evaluate-idea/<int:app_id>', methods=['POST'])
@login_required
def evaluate_idea(app_id):
    application = Application.query.get_or_404(app_id)
    action = request.form.get('action') 
    importance = request.form.get('importance', 'normal') 
    
    if action == 'accept':
        application.status = 'accepted'
        application.trainer_id = current_user.id 
        application.importance_level = importance 
        db.session.commit()
        flash('تم قبول الفكرة وانضمام الرائد إليك بنجاح!', 'success')
    elif action == 'reject':
        application.status = 'rejected'
        db.session.commit()
        flash('تم رفض الفكرة.', 'info')
        
    return redirect(url_for('trainer.ideas_pool'))

# ==========================================
# نظام الكورسات المتطور (LMS)
# ==========================================

@trainer_bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    if request.method == 'POST':
        title = request.form.get('title')
        program_id = request.form.get('program_id')
        description = request.form.get('description')
        
        new_course = TrainerCourse(
            trainer_id=current_user.id,
            program_id=program_id,
            title=title,
            description=description
        )
        db.session.add(new_course)
        db.session.commit()
        flash('تم إنشاء الكورس الأساسي. ابدأ الآن ببناء دروسك!', 'success')
        return redirect(url_for('trainer.course_editor', course_id=new_course.id))
        
    my_courses = TrainerCourse.query.filter_by(trainer_id=current_user.id).order_by(TrainerCourse.created_at.desc()).all()
    active_programs = Program.query.filter_by(status='open').all()
    return render_template('trainer/courses.html', courses=my_courses, programs=active_programs)

@trainer_bp.route('/course-editor/<int:course_id>', methods=['GET', 'POST'])
@login_required
def course_editor(course_id):
    course = TrainerCourse.query.get_or_404(course_id)
    
    if course.trainer_id != current_user.id:
        flash('غير مصرح لك بتعديل هذا الكورس', 'error')
        return redirect(url_for('trainer.courses'))

    if request.method == 'POST':
        title = request.form.get('title')
        order_num = request.form.get('order_num', 1)
        text_content = request.form.get('text_content')
        link_url = request.form.get('link_url')
        quiz_data = request.form.get('quiz_data')
        
        video_path = None
        pdf_path = None
        image_path = None
        
        save_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'lessons')
        os.makedirs(save_dir, exist_ok=True)
        
        if 'course_video' in request.files:
            file = request.files['course_video']
            if file and file.filename:
                fname = secure_filename(f"vid_{course.id}_{file.filename}")
                file.save(os.path.join(save_dir, fname))
                video_path = f"uploads/lessons/{fname}"
                
        if 'course_pdf' in request.files:
            file = request.files['course_pdf']
            if file and file.filename:
                fname = secure_filename(f"pdf_{course.id}_{file.filename}")
                file.save(os.path.join(save_dir, fname))
                pdf_path = f"uploads/lessons/{fname}"
                
        if 'course_image' in request.files:
            file = request.files['course_image']
            if file and file.filename:
                fname = secure_filename(f"img_{course.id}_{file.filename}")
                file.save(os.path.join(save_dir, fname))
                image_path = f"uploads/lessons/{fname}"

        new_lesson = CourseLesson(
            course_id=course.id,
            title=title,
            order_num=order_num,
            text_content=text_content,
            video_path=video_path,
            pdf_path=pdf_path,
            image_path=image_path,
            link_url=link_url,
            quiz_data=quiz_data
        )
        db.session.add(new_lesson)
        db.session.commit()
        flash('تم إضافة الدرس بكل محتوياته بنجاح!', 'success')
        return redirect(url_for('trainer.course_editor', course_id=course.id))

    return render_template('trainer/course_editor.html', course=course)

# ================= APIs الخاصة بالذكاء الاصطناعي للمدرب =================

@trainer_bp.route('/api/generate-lesson-text', methods=['POST'])
@login_required
def generate_lesson_text():
    data = request.get_json()
    prompt_text = data.get('prompt', '')
    
    prompt = f"""
    أنت خبير في ريادة الأعمال وصناعة المحتوى التعليمي.
    قم بكتابة محتوى تعليمي مفصل وراقي لهذا الموضوع: "{prompt_text}".
    استخدم تنسيق HTML (مثل <h3>, <ul>, <li>, <strong>, <p>) ليكون منسقاً وجاهزاً للعرض في منصة تعليمية.
    لا تكتب أي شيء خارج كود الـ HTML.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt)
        html_content = response.text.replace('```html', '').replace('```', '').strip()
        return jsonify({'status': 'success', 'content': html_content})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'حدث خطأ في توليد المحتوى. حاول مرة أخرى.'})

@trainer_bp.route('/api/generate-quiz', methods=['POST'])
@login_required
def generate_quiz():
    data = request.get_json()
    lesson_title = data.get('title', '')
    
    prompt = f"""
    قم بإنشاء اختبار قصير (3 أسئلة اختيارات متعددة) باللغة العربية للدرس الذي عنوانه: "{lesson_title}".
    الرد يجب أن يكون JSON صالح فقط بهذا التنسيق (بدون markdown):
    [
      {{"question": "السؤال الأول؟", "options": ["أ", "ب", "ج", "د"], "correct": 0}}
    ]
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt)
        json_str = response.text.replace('```json', '').replace('```', '').strip()
        return jsonify({'status': 'success', 'quiz': json.loads(json_str)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'تعذر توليد الاختبار.'})