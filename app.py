from flask import Flask, render_template, redirect, url_for,request,jsonify
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_babel import Babel
from flask import session, request

import os
import secrets
from routes.investor import investor_bp
from models import Service , ServicePurchase
from datetime import datetime


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///rafidain_incubator.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    app.config['MAX_FORM_MEMORY_SIZE'] = 100 * 1024 * 1024
    app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY', '')
    app.config['STRIPE_PUBLISHABLE_KEY'] = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    app.config['STRIPE_WEBHOOK_SECRET'] = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    app.config['BABEL_DEFAULT_LOCALE'] = 'ar'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
    import stripe
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    app.config['MAIL_SERVER'] = 'mail.privateemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'info@nawatech.org')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = ('نواتك', app.config['MAIL_USERNAME'])
    from flask_mail import Mail, Message
    mail = Mail(app)

    def send_payment_success_email(purchase):
        """إرسال إيميل نجاح الدفع باستخدام Namecheap"""
        try:
            msg = Message(
                subject="✅ تم تأكيد دفعك بنجاح - نواتك",
                recipients=[purchase.email],
                sender=("نواتك", app.config['MAIL_USERNAME'])
            )
            
            msg.html = f"""
            <h2>شكراً لثقتكم بـ نواتك</h2>
            <p>تم تأكيد استلام دفعة باقة <strong>{purchase.service.title}</strong> بنجاح.</p>
            
            <p>لقد تم تفعيل طلبكم في نظامنا، وفريقنا المختص سيباشر في إجراءات التنفيذ لضمان حصولكم على أفضل تجربة رقمية.</p>
            
            <p>سنوافيكم بالتحديثات أو روابط الوصول في أقرب وقت ممكن.</p>
            
            <br>
            <p style="font-weight:bold; color:#1a237e;">نحن فخورون بانضمامكم إلى بيئتنا الريادية 🚀</p>
            
            <hr>
            <small>إذا كان لديك أي استفسار، يرجى التواصل معنا على info@nawatech.org</small>
            """
            
            mail.send(msg)
            print(f"✅ تم إرسال إيميل نجاح الدفع إلى: {purchase.email}")
            
        except Exception as e:
            print(f"❌ فشل إرسال الإيميل إلى {purchase.email}: {str(e)}")
    
    # Configuration for file uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads', 'ids')
    
    # Ensure the upload foldehassan ali her exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # تهيئة الإضافات
    from models import db, User
    db.init_app(app)
    
    # تهيئة نظام تسجيل الدخول
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
    login_manager.login_message_category = 'info'
    
    def get_locale():
        return session.get('language', 'ar')

    babel = Babel(app, locale_selector=get_locale)
    @app.route('/set-language/<lang>')
    def set_language(lang):
        if lang in ['ar', 'en']:
            session['language'] = lang
        # العودة إلى نفس الصفحة التي كان فيها المستخدم
        return redirect(request.referrer or url_for('dashboard.index'))
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.filter_by(id=int(user_id)).first()
    
    # تسجيل المسارات (Blueprints)
    try:
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp)
    except ImportError:
        print("Warning: auth routes not found")
    
    try:
        from routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp)
    except ImportError:
        print("Warning: dashboard routes not found")
    
    try:
        from routes.advisor import advisor_bp
        app.register_blueprint(advisor_bp)
    except ImportError:
        print("Warning: advisor routes not found")
    
    try:
        from routes.trainer import trainer_bp
        app.register_blueprint(trainer_bp)
    except ImportError:
        print("Warning: trainer routes not found")


    try:
        from routes.investor import investor_bp
        app.register_blueprint(investor_bp)
    except ImportError:
        print("Warning: trainer routes not found")

    
    # إنشاء البرامج الأساسية إذا لم توجد
    def create_sample_data():
        try:
            from models import Program, TrainingModule
            
            # إنشاء برامج تجريبية
            if Program.query.count() == 0:
                programs = [
                    Program(
                        name='برنامج نواتك الأساسي',
                        type='incubator',
                        cohort_code='RFDN-2024-01',
                        city='بغداد',
                        status='open',
                        description='برنامج شامل لدعم الشركات الناشئة من مرحلة الفكرة إلى النمو'
                    ),
                    Program(
                        name='مسرعة الأعمال التقنية',
                        type='accelerator',
                        cohort_code='TECH-2024-01',
                        city='أربيل',
                        status='open',
                        description='برنامج متخصص للشركات الناشئة التقنية'
                    ),
                    Program(
                        name='منحة الابتكار الاجتماعي',
                        type='grant',
                        cohort_code='SOC-2024-01',
                        city='البصرة',
                        status='open',
                        description='دعم المشاريع ذات الأثر الاجتماعي'
                    )
                ]
                
                for program in programs:
                    db.session.add(program)
                
                # إنشاء وحدات تدريبية أساسية
                if TrainingModule.query.count() == 0:
                    modules = [
                        TrainingModule(
                            code='GE-101',
                            title='نمذجة نموذج العمل التجاري',
                            sector='general',
                            level='basic',
                            content_url='#',
                            is_active=True
                        ),
                        TrainingModule(
                            code='FT-101',
                            title='أساسيات التكنولوجيا المالية',
                            sector='fintech',
                            level='basic',
                            content_url='#',
                            is_active=True
                        ),
                        TrainingModule(
                            code='PM-201',
                            title='قياس الملاءمة منتج/سوق',
                            sector='general',
                            level='intermediate',
                            content_url='#',
                            is_active=True
                        )
                    ]
                    
                    for module in modules:
                        db.session.add(module)
                
                db.session.commit()
                print("تم إنشاء البيانات التجريبية بنجاح")
                
        except Exception as e:
            print(f"خطأ في إنشاء البيانات التجريبية: {e}")

    # الصفحة الرئيسية
    @app.route('/')
    def index():
        """الصفحة الرئيسية"""
        # عرض الصفحة الرئيسية للجميع (مسجل دخول أو لا)
        try:
            from models import Program, User, Startup
            
            stats = {
                'programs_count': Program.query.filter_by(status='open').count(),
                'startups_count': Startup.query.count() if Startup.query.first() else 0,
                'mentors_count': User.query.filter(User.role.in_(['Advisor', 'Trainer'])).count(),
                'success_stories': 12
            }
            
            # البرامج المتاحة
            featured_programs = Program.query.filter_by(status='open').limit(3).all()
        except:
            stats = {'programs_count': 0, 'startups_count': 0, 'mentors_count': 0, 'success_stories': 0}
            featured_programs = []
        
        return render_template('main/index.html', stats=stats, programs=featured_programs)
    
    @app.route('/programs')
    def programs():
        """صفحة البرامج"""
        try:
            from models import Program
            programs = Program.query.filter_by(status='open').order_by(Program.start_date).all()
        except:
            programs = []
        return render_template('main/programs.html', programs=programs)
    @app.route('/privacy-policy')
    def privacy_policy():
        return render_template('main/privacy_policy.html')

    @app.route('/services')
    def services():
        """صفحة خدماتنا (الواجهة العامة)"""
        services_list = Service.query.all()
        
        # إذا كانت قاعدة البيانات فارغة، نزرع الكروت الأربعة التي طلبتها أوتوماتيكياً
        if not services_list:
            initial_services =[
                Service(title="الشريك الاستراتيجي | Development Partner", 
                        description="مخصص للمستثمرين والشركاء الراغبين في دعم البنية التحتية لحاضنة Nawatech. تمول مساهمتك البحث والتطوير مقابل حقوق أولوية وفي المجلس الاستشاري.", 
                        price="10,000", button_text="Become a Partner", icon="fas fa-handshake"),
                        
                Service(title="Enterprise Advisory & Growth", 
                        description="احصل على استشارات متكاملة تغطي الجوانب القانونية، المالية، والتقنية للشركات الناشئة الطموحة.", 
                        price="5,000", button_text="Book Advisory Session", icon="fas fa-chart-line"),
                        
                Service(title="Digital Incubation & Training", 
                        description="استثمر في التدريب وإدارة الأعمال الرقمية المصممة خصيصاً للسوق العراقي.", 
                        price="1,000", button_text="Enroll in Training", icon="fas fa-laptop-code"),
                        
                Service(title="Early Access Licensing", 
                        description="كن من أوائل الحاصلين على التراخيص وساهم في تخصيص الميزات البرمجية التي يحتاجها نشاطك التجاري.", 
                        price="2,000", button_text="Secure Early License", icon="fas fa-key")
            ]
            db.session.add_all(initial_services)
            db.session.commit()
            services_list = Service.query.all()

        return render_template('main/services.html', services=services_list)
    
    

    @app.route('/about')
    def about():
        """صفحة حول"""
        return render_template('main/about.html')
    
    @app.route('/contact')
    def contact():
        """صفحة التواصل"""
        return render_template('main/contact.html')
    # إنشاء الجداول عند التشغيل الأول
    with app.app_context():
        try:
            db.create_all()
            
            # إنشاء حساب مدير إذا لم يوجد
            admin = User.query.filter_by(role='Admin').first()
            
            if not admin:
                # حذف أي حسابات موجودة مسبقاً لضمان البيانات الصحيحة
                existing_emails = [
                    'admin@rafidain.com', 
                    'advisor@rafidain.com', 
                    'trainer@rafidain.com',
                    'founder@rafidin.com'
                ]
                User.query.filter(User.email.in_(existing_emails)).delete(synchronize_session=False)
                db.session.commit()
                
                admin = User(
                    full_name='د. عمر الإداري',
                    email='admin@rafidain.com',
                    role='Admin',
                    is_active=True
                )
                admin.set_password(os.getenv('DEMO_ADMIN_PASSWORD') or secrets.token_urlsafe(24))
                db.session.add(admin)
                
                # إضافة مستشار
                advisor = User(
                    full_name='د. سارة أحمد - مستشارة أعمال',
                    email='advisor@rafidain.com',
                    role='Advisor',
                    is_active=True
                )
                advisor.set_password(os.getenv('DEMO_ADVISOR_PASSWORD') or secrets.token_urlsafe(24))
                db.session.add(advisor)
                
                # إضافة مدرب
                trainer = User(
                    full_name='أ. محمد علي - مدرب معتمد',
                    email='trainer@rafidain.com',
                    role='Trainer',
                    is_active=True
                )
                trainer.set_password(os.getenv('DEMO_TRAINER_PASSWORD') or secrets.token_urlsafe(24))
                db.session.add(trainer)
                
                # إضافة رائد أعمال تجريبي
                founder = User(
                    full_name='م. أحمد محمد - رائد أعمال',
                    email='founder@rafidain.com',
                    role='Founder',
                    is_active=True
                )
                founder.set_password(os.getenv('DEMO_FOUNDER_PASSWORD') or secrets.token_urlsafe(24))
                db.session.add(founder)
                
                db.session.commit()
                print("=" * 60)
                print("✅ تم إنشاء الحسابات التجريبية بنجاح!")
                print("=" * 60)
                print("📋 حسابات للاختبار:")
                print("-" * 30)
                print("🔐 المدير (Admin):")
                print("   📧 admin@rafidain.com")
                print("   🔑 configured via environment variable")
                print("")
                print("👨‍💼 المستشار (Advisor):")
                print("   📧 advisor@rafidain.com")
                print("   🔑 configured via environment variable")
                print("")
                print("👨‍🏫 المدرب (Trainer):")
                print("   📧 trainer@rafidain.com")
                print("   🔑 configured via environment variable")
                print("")
                print("🚀 رائد الأعمال (Founder):")
                print("   📧 founder@rafidain.com")
                print("   🔑 configured via environment variable")
                print("=" * 60)
                print("📊 للتأكد من البيانات:")
                print(f"   عدد المستخدمين: {User.query.count()}")
                print(f"   المدراء: {User.query.filter_by(role='Admin').count()}")
                print(f"   المستشارين: {User.query.filter_by(role='Advisor').count()}")
                print(f"   المدربين: {User.query.filter_by(role='Trainer').count()}")
                print(f"   رواد الأعمال: {User.query.filter_by(role='Founder').count()}")
                print("=" * 60)
            else:
                # التأكد من وجود جميع الحسابات
                advisor_exists = User.query.filter_by(email='advisor@rafidain.com').first()
                trainer_exists = User.query.filter_by(email='trainer@rafidain.com').first()
                founder_exists = User.query.filter_by(email='founder@rafidain.com').first()
                
                if not advisor_exists:
                    advisor = User(
                        full_name='د. سارة أحمد - مستشارة أعمال',
                        email='advisor@rafidain.com',
                        role='Advisor',
                        is_active=True
                    )
                    advisor.set_password(os.getenv('DEMO_ADVISOR_PASSWORD') or secrets.token_urlsafe(24))
                    db.session.add(advisor)
                    print("✅ تم إنشاء حساب المستشار")
                
                if not trainer_exists:
                    trainer = User(
                        full_name='أ. محمد علي - مدرب معتمد',
                        email='trainer@rafidain.com',
                        role='Trainer',
                        is_active=True
                    )
                    trainer.set_password(os.getenv('DEMO_TRAINER_PASSWORD') or secrets.token_urlsafe(24))
                    db.session.add(trainer)
                    print("✅ تم إنشاء حساب المدرب")
                
                if not founder_exists:
                    founder = User(
                        full_name='م. أحمد محمد - رائد أعمال',
                        email='founder@rafidain.com',
                        role='Founder',
                        is_active=True
                    )
                    founder.set_password(os.getenv('DEMO_FOUNDER_PASSWORD') or secrets.token_urlsafe(24))
                    db.session.add(founder)
                    print("✅ تم إنشاء حساب رائد الأعمال")
                
                if not advisor_exists or not trainer_exists or not founder_exists:
                    db.session.commit()
                
                print("=" * 60)
                print("📊 إحصائيات الحسابات الحالية:")
                print(f"   المدراء: {User.query.filter_by(role='Admin').count()}")
                print(f"   المستشارين: {User.query.filter_by(role='Advisor').count()}")
                print(f"   المدربين: {User.query.filter_by(role='Trainer').count()}")
                print(f"   رواد الأعمال: {User.query.filter_by(role='Founder').count()}")
                print("=" * 60)
            
            # إنشاء البيانات التجريبية
            create_sample_data()
            
        except Exception as e:
            print(f"خطأ في إنشاء قاعدة البيانات: {e}")
    
    # إضافة routes إدارية جديدة للمدير
    @app.route('/admin/system-settings')
    def admin_system_settings():
        """إعدادات النظام للمدير فقط"""
        from flask_login import current_user
        if not current_user.is_authenticated or current_user.role != 'Admin':
            return redirect(url_for('auth.login'))
        
        return render_template('admin/system_settings.html')

    @app.route('/admin/user-permissions')
    def admin_user_permissions():
        """إدارة صلاحيات المستخدمين"""
        from flask_login import current_user
        if not current_user.is_authenticated or current_user.role != 'Admin':
            return redirect(url_for('auth.login'))
        
        return render_template('admin/user_permissions.html')

    @app.route('/admin/activity-logs')
    def admin_activity_logs():
        """سجل نشاطات النظام"""
        from flask_login import current_user
        if not current_user.is_authenticated or current_user.role != 'Admin':
            return redirect(url_for('auth.login'))
        
        return render_template('admin/activity_logs.html')
    
    @app.route('/terms-of-service')
    def terms_of_service():
        """صفحة شروط الخدمة"""
        return render_template('main/terms_of_service.html')


    @app.route('/refund-policy')
    def refund_policy():
        """صفحة سياسة الاسترداد"""
        return render_template('main/refund_policy.html')
    

    @app.route('/create-checkout-session', methods=['POST'])
    def create_checkout_session():
        try:
            service_id = request.form.get('service_id')
            if not service_id:
                return "لم يتم إرسال معرف الخدمة", 400

            service = Service.query.get_or_404(service_id)

            # تنظيف السعر
            price_str = str(service.price).replace(',', '').replace(' ', '').strip()
            try:
                unit_amount = int(float(price_str) * 100)
            except:
                return f"خطأ في السعر: {service.price}", 400

            # إنشاء الجلسة مع تتبع واضح
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': service.currency.lower(),           # نستخدم MYR حالياً
                        'product_data': {
                            'name': service.title[:80],
                            'description': service.description[:200] or "خدمة من نواتك",
                        },
                        'unit_amount': unit_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('services', _external=True),
                metadata={
                    'service_id': str(service.id),
                    'service_title': service.title,
                    'email': request.form.get('email', 'no@email.com'),
                    'full_name': request.form.get('full_name', 'عميل'),
                    'phone': request.form.get('phone', ''),
                    'country': request.form.get('country', 'IQ')
                }
            )

            print(f"✅ جلسة دفع تم إنشاؤها بنجاح | Service: {service.title} | Amount: {unit_amount/100} MYR")
            print(f"🔗 رابط الدفع: {checkout_session.url}")

            return redirect(checkout_session.url, code=303)

        except stripe.error.StripeError as e:
            error_msg = str(e)
            print("🔴 Stripe Error:", error_msg)
            return f"خطأ من Stripe: {error_msg}", 500

        except Exception as e:
            print("🔴 خطأ عام:", str(e))
            return f"حدث خطأ غير متوقع: {str(e)}", 500

    @app.route('/payment/success')
    def payment_success():
        session_id = request.args.get('session_id')
        
        # يمكنك تحسينها لاحقاً بجلب البيانات من Stripe إذا أردت
        service_title = request.args.get('service_title', 'الخدمة')
        
        return render_template('main/payment_success.html', 
                            session_id=session_id,
                            service_title=service_title)

    @app.route('/stripe-webhook', methods=['POST'])
    def stripe_webhook():
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, app.config['STRIPE_WEBHOOK_SECRET']
            )
        except Exception as e:
            print("Webhook signature verification failed:", str(e))
            return "Invalid signature", 400

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})

            try:
                purchase = ServicePurchase(
                    email=metadata.get('email'),
                    full_name=metadata.get('full_name'),
                    phone=metadata.get('phone'),
                    country=metadata.get('country'),
                    service_id=int(metadata.get('service_id')),
                    amount=str(session.get('amount_total', 0) / 100),
                    stripe_session_id=session['id'],
                    status='paid',
                    paid_at=datetime.utcnow()
                )
                db.session.add(purchase)
                db.session.commit()
                send_payment_success_email(purchase)
                print(f"✅ دفعة جديدة مسجلة: {metadata.get('full_name')} - {session.get('amount_total', 0)/100} SAR")
            except Exception as e:
                print("Error saving purchase to database:", str(e))

        return '', 200

# ====================== Route خاص بطلب الشراكة (Become a Partner) ======================
    @app.route('/submit-partner-request', methods=['POST'])
    def submit_partner_request():
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            country = request.form.get('country')
            reason = request.form.get('reason')

            if not all([name, email, reason]):
                return jsonify({"status": "error", "message": "يرجى ملء جميع الحقول المطلوبة"}), 400

            # إرسال الإيميل إلى info@nawatech.org
            msg = Message(
                subject="🔔 طلب شراكة جديد من موقع نواتك",
                recipients=["info@nawatech.org"],
                sender=("نواتك", app.config['MAIL_USERNAME'])
            )

            msg.html = f"""
            <h2>طلب شراكة جديد</h2>
            <p><strong>الاسم:</strong> {name}</p>
            <p><strong>البريد الإلكتروني:</strong> {email}</p>
            <p><strong>رقم الهاتف:</strong> {phone or 'غير محدد'}</p>
            <p><strong>الدولة:</strong> {country or 'غير محدد'}</p>
            <hr>
            <p><strong>لماذا يرغب في الشراكة؟</strong></p>
            <p style="background:#f8f9fa; padding:15px; border-radius:8px;">
                {reason}
            </p>
            <br>
            <small>تم الإرسال في: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</small>
            """

            mail.send(msg)

            return jsonify({"status": "success", "message": "تم إرسال طلبك بنجاح!"})

        except Exception as e:
            print("Error in partner request:", str(e))
            return jsonify({"status": "error", "message": "حدث خطأ أثناء إرسال الطلب"}), 500

    return app

    # تأكد من استيراد الجدول في أعلى الملف


    
# إنشاء التطبيق
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)