from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(40))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Founder, Trainer, Advisor, Investor, Admin
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # حقول التحقق من الهوية
    id_front_path = db.Column(db.String(255), nullable=True)
    id_back_path = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(80), nullable=True) 
    commercial_register_path = db.Column(db.String(255), nullable=True) 
    verification_status = db.Column(db.String(20), default='unverified', nullable=False)

    # ────────────────────────────────────────────────
    # العلاقات – كلها بـ back_populates (متسقة وآمنة)
    # ────────────────────────────────────────────────
    
    startups = db.relationship(
        "Startup",
        back_populates="owner",
        lazy="select",
        cascade="all, delete-orphan"
    )

    courses = db.relationship(
        "TrainerCourse",
        back_populates="trainer",
        lazy="select"
    )

    trained_applications = db.relationship(
        "Application",
        back_populates="trainer",
        lazy="select",
        foreign_keys="Application.trainer_id"
    )

    mentoring_sessions = db.relationship(
        "MentoringSession",
        back_populates="trainer",
        foreign_keys="MentoringSession.trainer_id",
        lazy="select"
    )

    # إذا أضفت لاحقًا علاقة مع الممولين (كما في Application.investor_id)
    funded_applications = db.relationship(
         "Application",
         back_populates="investor",
         foreign_keys="Application.investor_id",
         lazy="select"
     )
    sent_advisor_messages = db.relationship(
        'AdvisorMessage',
        foreign_keys='AdvisorMessage.advisor_id',
        back_populates='advisor',
        lazy='select',
        cascade='all, delete-orphan')   # اختياري: لحذف الرسائل إذا حُذف المستشار)

    # علاقة جديدة: الرسائل التي وصلت إلى المدرب من المستشار
    received_advisor_messages = db.relationship(
        'AdvisorMessage',
        foreign_keys='AdvisorMessage.trainer_id',
        back_populates='trainer',
        lazy='select'
    )

    # ────────────────────────────────────────────────
    # الدوال والخصائص
    # ────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_verified(self) -> bool:
        return self.verification_status == 'verified'

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    @property
    def is_trainer(self) -> bool:
        return self.role == 'trainer'

    @property
    def is_investor(self) -> bool:
        return self.role == 'investor'

    def __repr__(self) -> str:
        return f"<User {self.full_name} ({self.email}) - Role: {self.role}>"


class Startup(db.Model):
    __tablename__ = 'startups'

    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(140), nullable=False)
    sector = db.Column(db.String(80), nullable=False)
    stage = db.Column(db.String(40), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    summary = db.Column(db.Text, nullable=False)

    problem = db.Column(db.Text)
    solution = db.Column(db.Text)
    target_market = db.Column(db.Text)
    business_model = db.Column(db.Text)
    competitive_advantage = db.Column(db.Text)

    team_size = db.Column(db.String(20))
    key_skills = db.Column(db.String(255))
    team_experience = db.Column(db.Text)

    funding_stage = db.Column(db.String(30))
    funding_amount = db.Column(db.Integer)
    current_revenue = db.Column(db.Integer)
    revenue_projection = db.Column(db.Integer)

    prototype_type = db.Column(db.String(20), default='none')
    prototype_path = db.Column(db.String(255), nullable=True)
    prototype_data = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    owner = db.relationship("User", back_populates="startups", lazy="select")

    applications = db.relationship("Application", back_populates="startup", lazy="select")
    training_assignments = db.relationship("TrainingAssignment", back_populates="startup", lazy="select")
    evaluation = db.relationship("StartupEvaluation", back_populates="startup", uselist=False, lazy="select")


class CourseLesson(db.Model):
    __tablename__ = 'course_lessons'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('trainer_courses.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    order_num = db.Column(db.Integer, default=1) # رقم الدرس الذي يختاره المدرب
    
    # الدرس الواحد يمكن أن يحتوي على كل هذه الأنواع معاً
    text_content = db.Column(db.Text, nullable=True)    # نص الشرح (مكتوب بواسطة المدرب أو الذكاء الاصطناعي)
    video_path = db.Column(db.String(255), nullable=True) # مسار الفيديو
    pdf_path = db.Column(db.String(255), nullable=True)   # مسار الملف
    image_path = db.Column(db.String(255), nullable=True) # مسار الصورة
    link_url = db.Column(db.String(255), nullable=True)   # رابط خارجي
    quiz_data = db.Column(db.Text, nullable=True)       # بيانات الاختبار (JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    course = db.relationship('TrainerCourse', back_populates='lessons')
class Program(db.Model):
    __tablename__ = 'programs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    type = db.Column(db.String(20))
    cohort_code = db.Column(db.String(40))
    city = db.Column(db.String(80))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='open')
    description = db.Column(db.Text)

    applications = db.relationship("Application", back_populates="program", lazy="select")
    trainer_courses = db.relationship("TrainerCourse", back_populates="program", lazy="select")


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startups.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    
    trainer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    importance_level = db.Column(db.String(20), default='normal')
    
    # الحقول الجديدة الخاصة بمشروع التخرج + المتابعة
    final_project_file = db.Column(db.String(255), nullable=True)
    final_project_text = db.Column(db.Text, nullable=True)
    final_project_submitted = db.Column(db.Boolean, default=False)
    trainer_feedback = db.Column(db.Text, nullable=True)
    forwarded_to_advisor = db.Column(db.Boolean, default=False)
    
    # حقول متابعة الاستمارات والمشروع
    form_one_submitted = db.Column(db.Boolean, default=False)   # هل أرسل الرائد استمارة 1؟
    form_one_viewed = db.Column(db.Boolean, default=False)      # هل شاهد المدرب الاستمارة؟
    project_viewed = db.Column(db.Boolean, default=False)       # هل شاهد المدرب المشروع النهائي؟
    
    is_graduated = db.Column(db.Boolean, default=False)         # هل تم منحه الشهادة؟
    investor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # الممول المهتم
    
    score = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='submitted')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ────────────────────────────────────────────────
    # العلاقات – كلها بـ back_populates (متسقة وآمنة)
    # ────────────────────────────────────────────────
    
    startup = db.relationship("Startup", back_populates="applications", lazy="select")
    program = db.relationship("Program", back_populates="applications", lazy="select")
    
    trainer = db.relationship(
        "User",
        back_populates="trained_applications",
        foreign_keys=[trainer_id],
        lazy="select"
    )
    
    investor = db.relationship(
        "User",
        back_populates="funded_applications",
        foreign_keys=[investor_id],
        lazy="select"
    )
    
    lesson_progress = db.relationship(
        "LessonProgress",
        back_populates="application",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    form_one_submission = db.relationship(
        "FormOneSubmission",
        back_populates="application",
        uselist=False,  # استمارة واحدة فقط لكل طلب
        lazy="select"
    )
    
    mentoring_sessions = db.relationship(
        "MentoringSession",
        back_populates="application",
        lazy="select",
        cascade="all, delete-orphan"
    )

class MentoringSession(db.Model):
    __tablename__ = 'mentoring_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    requested_date = db.Column(db.String(20), nullable=False)
    requested_time = db.Column(db.String(20), nullable=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, approved, rescheduled, completed, cancelled...
    
    room_name = db.Column(db.String(100), nullable=False)  # للاجتماعات المباشرة
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات – استخدام back_populates للتوافق
    application = db.relationship(
        'Application',
        back_populates='mentoring_sessions',
        lazy='select'
    )
    
    trainer = db.relationship(
        'User',
        back_populates='mentoring_sessions',   # اختر اسمًا مناسبًا غير مستخدم
        foreign_keys=[trainer_id],
        lazy='select'
    )
class FormOneSubmission(db.Model):
    __tablename__ = 'form_one_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    
    customer_needs = db.Column(db.Text, nullable=False)  # ماذا وأين ولمن؟
    ultimate_goal   = db.Column(db.Text, nullable=False)  # الهدف الأسمى
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقة – استخدم back_populates بدلاً من backref
    application = db.relationship(
        'Application',
        back_populates='form_one_submission',   # اسم واضح وغير مستخدم من قبل
        lazy='select'
    )
class StartupEvaluation(db.Model):
    __tablename__ = 'startup_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startups.id'), nullable=False)

    idea_score = db.Column(db.Integer)
    team_score = db.Column(db.Integer)
    market_score = db.Column(db.Integer)
    tech_score = db.Column(db.Integer)
    total_score = db.Column(db.Float)

    analysis_summary = db.Column(db.Text)
    recommendation = db.Column(db.Text)

    # الحقل الجديد لمصفوفة المخاطر (يمكن تخزينه كـ HTML أو JSON string أو نص طويل)
    risk_matrix = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقة – back_populates بدلاً من backref + db.backref
    startup = db.relationship('Startup', back_populates='evaluation', uselist=False)

class TrainingModule(db.Model):
    __tablename__ = 'training_modules'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True)
    title = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(80))
    level = db.Column(db.String(20))
    content_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    assignments = db.relationship("TrainingAssignment", back_populates="module", lazy="select")


class TrainingAssignment(db.Model):
    __tablename__ = 'training_assignments'

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startups.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('training_modules.id'), nullable=False)

    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    score = db.Column(db.Float, default=0)

    startup = db.relationship("Startup", back_populates="training_assignments", lazy="select")
    module = db.relationship("TrainingModule", back_populates="assignments", lazy="select")

    assessments = db.relationship("Assessment", back_populates="assignment", lazy="select")


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('training_assignments.id'), nullable=False)

    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    points = db.Column(db.Integer, default=1)
    earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignment = db.relationship("TrainingAssignment", back_populates="assessments", lazy="select")


class AdvisorDecision(db.Model):
    __tablename__ = 'advisor_decisions'

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startups.id'), nullable=False)
    advisor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    decision = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TrainerEvaluation(db.Model):
    __tablename__ = 'trainer_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startups.id'), nullable=False)
    trainer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    verdict = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startups.id'), nullable=False)
    certificate_code = db.Column(db.String(40), unique=True, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(255))
    qr_code = db.Column(db.String(255))


class FundingRequest(db.Model):
    __tablename__ = 'funding_requests'

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer, db.ForeignKey('startups.id'), nullable=False)
    amount_requested = db.Column(db.Numeric(18, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)


class TrainerCourse(db.Model):
    __tablename__ = 'trainer_courses'

    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات – استخدام back_populates في كلا الاتجاهين
    trainer = db.relationship('User', back_populates='courses')
    program = db.relationship('Program', back_populates='trainer_courses')

    # علاقة مع الدروس (one-to-many)
    lessons = db.relationship(
        'CourseLesson',
        back_populates='course',
        cascade="all, delete-orphan",
        order_by="CourseLesson.order_num"
    )


class LessonProgress(db.Model):
    __tablename__ = 'lesson_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    
    # نستخدم string لنحفظ فيه إما (رقم الدرس الخاص بالمدرب) أو (اسم الدرس التحضيري مثل prep_1)
    lesson_id = db.Column(db.String(100), nullable=False)
    
    is_completed = db.Column(db.Boolean, default=False)   # ← ملاحظة: default=False أكثر منطقية هنا
    completed_at = db.Column(db.DateTime, nullable=True)   # لا default إلا إذا تم إكماله فعلاً
    
    # العلاقة العكسية — استخدم back_populates بدلاً من backref
    application = db.relationship('Application', back_populates='lesson_progress')


class AdvisorMessage(db.Model):
    __tablename__ = 'advisor_messages'

    id = db.Column(db.Integer, primary_key=True)
    advisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات – استخدام back_populates للتوافق والأمان
    advisor = db.relationship(
        'User',
        foreign_keys=[advisor_id],
        back_populates='sent_advisor_messages',   # اسم واضح للرسائل المرسلة من المستشار
        lazy='select'
    )
    
    trainer = db.relationship(
        'User',
        foreign_keys=[trainer_id],
        back_populates='received_advisor_messages',  # اسم واضح للرسائل المستلمة من المستشار
        lazy='select'
    )


from datetime import datetime

# جدول يربط المشروع المرسل من المدرب إلى المستشار
class SharedProject(db.Model):
    __tablename__ = 'shared_projects'
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    advisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    application = db.relationship('Application')
    trainer = db.relationship('User', foreign_keys=[trainer_id])

# جدول رسائل الممولين للمدربين
class FundingMessage(db.Model):
    __tablename__ = 'funding_messages'
    id = db.Column(db.Integer, primary_key=True)
    investor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    investor = db.relationship('User', foreign_keys=[investor_id])
    application = db.relationship('Application')

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(50), nullable=False)
    button_text = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), default='fas fa-star') # أيقونة الكارت
    currency = db.Column(db.String(10), default='MYR')
    currency_symbol = db.Column(db.String(10), default='رنجت')
    is_special = db.Column(db.Boolean, default=False)
    special_form_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServicePurchase(db.Model):
    __tablename__ = 'service_purchases'

    id = db.Column(db.Integer, primary_key=True)
    
    # من يدفع (يمكن أن يكون مستخدم مسجل أو ضيف)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=True)
    country = db.Column(db.String(80), nullable=True)

    # الخدمة التي تم شراؤها
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    
    # بيانات الدفع
    amount = db.Column(db.String(50), nullable=False)           # السعر وقت الشراء
    currency = db.Column(db.String(10), default="SAR")
    stripe_session_id = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')        # pending, paid, failed
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='purchases', lazy=True)
    service = db.relationship('Service', backref='purchases', lazy=True)

    def __repr__(self):
        return f"<ServicePurchase {self.full_name} - {self.amount} - {self.status}>"