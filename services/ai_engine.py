import random
from typing import List, Dict, Any

class TrainingModuleSuggestion:
    def __init__(self, code: str, title: str, level: str):
        self.code = code
        self.title = title
        self.level = level

class QAItem:
    def __init__(self, question: str, correct_answer: str):
        self.question = question
        self.correct_answer = correct_answer

class PrivateAIEngine:
    """
    محرك الذكاء الاصطناعي المحلي - لا يتصل بأي خدمة خارجية
    """
    
    def __init__(self):
        self.module_templates = {
            'fintech': [
                {'code': 'FT-101', 'title': 'أساسيات التكنولوجيا المالية', 'level': 'basic'},
                {'code': 'FT-201', 'title': 'الامتثال المالي ومكافحة غسل الأموال', 'level': 'intermediate'},
                {'code': 'FT-301', 'title': 'الذكاء الاصطناعي في الخدمات المصرفية', 'level': 'advanced'},
            ],
            'agri': [
                {'code': 'AG-101', 'title': 'الزراعة الذكية وإنترنت الأشياء', 'level': 'basic'},
                {'code': 'AG-201', 'title': 'سلاسل الإمداد الزراعية', 'level': 'intermediate'},
                {'code': 'AG-301', 'title': 'الاستدامة والتحليلات المتقدمة', 'level': 'advanced'},
            ],
            'health': [
                {'code': 'HT-101', 'title': 'التكنولوجيا الصحية والرقمنة', 'level': 'basic'},
                {'code': 'HT-201', 'title': 'التطبيقات الطبية والخصوصية', 'level': 'intermediate'},
            ],
            'education': [
                {'code': 'ED-101', 'title': 'منصات التعليم الإلكتروني', 'level': 'basic'},
                {'code': 'ED-201', 'title': 'التعلم التفاعلي والذكي', 'level': 'intermediate'},
            ]
        }
        
        self.stage_modules = {
            'idea': [
                {'code': 'GE-101', 'title': 'نمذجة نموذج العمل التجاري', 'level': 'basic'},
                {'code': 'GE-102', 'title': 'بحث السوق وتحليل المنافسين', 'level': 'basic'},
            ],
            'prototype': [
                {'code': 'PM-201', 'title': 'قياس الملاءمة منتج/سوق', 'level': 'intermediate'},
                {'code': 'PM-202', 'title': 'التطوير السريع والاختبار', 'level': 'intermediate'},
            ],
            'traction': [
                {'code': 'GR-301', 'title': 'النمو والمقاييس المتقدمة', 'level': 'advanced'},
                {'code': 'GR-302', 'title': 'الاستراتيجيات التوسعية', 'level': 'advanced'},
            ]
        }

    def suggest_modules(self, sector: str, stage: str) -> List[TrainingModuleSuggestion]:
        """توليد حقائب تدريبية مخصصة حسب القطاع والمرحلة"""
        suggestions = []
        
        # إضافة وحدات حسب القطاع
        if sector:
            sector_key = self._normalize_sector(sector)
            if sector_key in self.module_templates:
                for module in self.module_templates[sector_key]:
                    suggestions.append(TrainingModuleSuggestion(
                        module['code'], module['title'], module['level']
                    ))
        
        # إضافة وحدات حسب المرحلة
        if stage and stage.lower() in self.stage_modules:
            for module in self.stage_modules[stage.lower()]:
                suggestions.append(TrainingModuleSuggestion(
                    module['code'], module['title'], module['level']
                ))
        
        # إضافة وحدات عامة إذا لم توجد
        if not suggestions:
            for module in self.stage_modules['idea']:
                suggestions.append(TrainingModuleSuggestion(
                    module['code'], module['title'], module['level']
                ))
        
        return suggestions

    def _normalize_sector(self, sector: str) -> str:
        """تطبيع اسم القطاع للبحث في القوالب"""
        if not sector:
            return 'general'
        
        sector_lower = sector.lower()
        if 'fintech' in sector_lower or 'مالي' in sector_lower:
            return 'fintech'
        elif 'agri' in sector_lower or 'زراع' in sector_lower:
            return 'agri'
        elif 'health' in sector_lower or 'صح' in sector_lower:
            return 'health'
        elif 'education' in sector_lower or 'تعليم' in sector_lower:
            return 'education'
        else:
            return 'general'

class ScoringService:
    """خدمة التقييم الآلي للطلبات"""
    
    @staticmethod
    def score_application(summary: str, sector: str, stage: str) -> float:
        """تقييم الطلب بناء على عوامل متعددة"""
        score = 0.0
        
        # تقييم الملخص (40 نقطة)
        if summary:
            summary_length = len(summary)
            if summary_length > 500:
                score += 40
            elif summary_length > 200:
                score += 30
            elif summary_length > 50:
                score += 20
            else:
                score += 10
        
        # تقييم المرحلة (30 نقطة)
        stage_scores = {
            'traction': 30,
            'prototype': 20,
            'idea': 10
        }
        score += stage_scores.get(stage, 10)
        
        # تقييم القطاع (20 نقطة)
        priority_sectors = ['fintech', 'health', 'agri', 'education']
        if sector and any(s in sector.lower() for s in priority_sectors):
            score += 20
        else:
            score += 10
        
        # عوامل إضافية (10 نقاط)
        score += 10
        
        return min(100.0, score)

class CertificateService:
    """خدمة إصدار الشهادات"""
    
    @staticmethod
    def issue_certificate(startup_id: int, startup_name: str) -> Dict[str, str]:
        """إصدار شهادة جديدة"""
        import time
        
        code = f"CERT-{startup_id}-{int(time.time())}"
        pdf_path = f"/static/certificates/{code}.pdf"
        qr_code = f"/static/qr/{code}.png"
        
        return {
            'code': code,
            'pdf_path': pdf_path,
            'qr_code': qr_code
        }
        """توليد إجابة مرجعية للسؤال"""
        
        # قاموس إجابات أساسية
        answers = {
            "ما هي العناصر الأساسية لنموذج العمل التجاري؟": "شرائح العملاء، القيمة المضافة، القنوات، علاقات العملاء، مصادر الدخل، الموارد الأساسية، الأنشطة الرئيسية، الشراكات، هيكل التكاليف",
            "كيف تحدد حجم السوق المستهدف؟": "من خلال تحليل TAM، SAM، SOM وجمع بيانات من مصادر أولية وثانوية",
            "ما أهمية الميزة التنافسية في المشروع؟": "تميز المنتج عن المنافسين وتضمن استدامة النمو",
            "اذكر ثلاث طرق لتحقيق الدخل في مشروعك؟": "الاشتراكات، البيع المباشر، العمولات",
        }
        
        return answers.get(question, "إجابة شاملة تغطي النقاط الأساسية للسؤال")

class ScoringService:
    """خدمة التقييم الآلي للطلبات"""
    
    @staticmethod
    def score_application(summary: str, sector: str, stage: str) -> float:
        """تقييم الطلب بناء على عوامل متعددة"""
        score = 0.0
        
        # تقييم الملخص (40 نقطة)
        if summary:
            summary_length = len(summary)
            if summary_length > 500:
                score += 40
            elif summary_length > 200:
                score += 30
            elif summary_length > 50:
                score += 20
            else:
                score += 10
        
        # تقييم المرحلة (30 نقطة)
        stage_scores = {
            'traction': 30,
            'prototype': 20,
            'idea': 10
        }
        score += stage_scores.get(stage, 10)
        
        # تقييم القطاع (20 نقطة)
        priority_sectors = ['fintech', 'health', 'agri', 'education']
        if any(s in sector.lower() for s in priority_sectors):
            score += 20
        else:
            score += 10
        
        # عوامل إضافية (10 نقاط)
        score += 10
        
        return min(100.0, score)

class CertificateService:
    """خدمة إصدار الشهادات"""
    
    @staticmethod
    def issue_certificate(startup_id: int, startup_name: str) -> Dict[str, str]:
        """إصدار شهادة جديدة"""
        import time
        
        code = f"CERT-{startup_id}-{int(time.time())}"
        pdf_path = f"/static/certificates/{code}.pdf"
        qr_code = f"/static/qr/{code}.png"
        
        # TODO: توليد PDF و QR فعلياً
        return {
            'code': code,
            'pdf_path': pdf_path,
            'qr_code': qr_code
        }
