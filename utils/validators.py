"""
أدوات التحقق من صحة البيانات - Validators
"""
import re
from datetime import datetime, timedelta
from typing import Tuple, Optional
import pytz
from config import config

class Validators:
    """أدوات التحقق من صحة البيانات"""
    
    @staticmethod
    def validate_player_id(player_id: str) -> Tuple[bool, Optional[str]]:
        """التحقق من صحة Player ID"""
        if not player_id:
            return False, "❌ معرف اللاعب مطلوب"
        
        # يجب أن يكون رقمياً
        if not player_id.isdigit():
            return False, "❌ معرف اللاعب يجب أن يكون رقمياً"
        
        # الطول المناسب (عادة 5-10 أرقام)
        if len(player_id) < 5 or len(player_id) > 15:
            return False, "❌ معرف اللاعب يجب أن يكون بين 5-15 رقم"
        
        return True, None
    
    @staticmethod
    def validate_player_name(name: str) -> Tuple[bool, Optional[str]]:
        """التحقق من صحة اسم اللاعب"""
        if not name or len(name.strip()) == 0:
            return False, "❌ اسم اللاعب مطلوب"
        
        if len(name) < 2:
            return False, "❌ اسم اللاعب قصير جداً"
        
        if len(name) > 50:
            return False, "❌ اسم اللاعب طويل جداً (الحد الأقصى 50 حرف)"
        
        return True, None
    
    @staticmethod
    def validate_alliance_name(name: str) -> Tuple[bool, Optional[str]]:
        """التحقق من صحة اسم التحالف"""
        if not name or len(name.strip()) == 0:
            return False, "❌ اسم التحالف مطلوب"
        
        if len(name) < 2:
            return False, "❌ اسم التحالف قصير جداً"
        
        if len(name) > 50:
            return False, "❌ اسم التحالف طويل جداً (الحد الأقصى 50 حرف)"
        
        return True, None

    @staticmethod
    def validate_alliance_tag(tag: str) -> Tuple[bool, Optional[str]]:
        """التحقق من رمز التحالف (3 أحرف/أرقام)"""
        if not tag or len(tag.strip()) == 0:
            return False, "❌ رمز التحالف مطلوب"

        clean_tag = tag.strip().upper()
        if len(clean_tag) != 3:
            return False, "❌ رمز التحالف يجب أن يكون 3 أحرف"

        if not re.match(r'^[A-Z0-9]{3}$', clean_tag):
            return False, "❌ رمز التحالف يجب أن يحتوي أحرف/أرقام إنجليزية فقط"

        return True, None
    
    @staticmethod
    def validate_datetime(date_str: str, time_str: str) -> Tuple[bool, Optional[datetime], Optional[str]]:
        """التحقق من صحة التاريخ والوقت"""
        try:
            # محاولة تحليل التاريخ (YYYY-MM-DD)
            datetime_str = f"{date_str} {time_str}"
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            
            # تحويل إلى المنطقة الزمنية المحددة
            tz = pytz.timezone(config.TIMEZONE)
            dt = tz.localize(dt)
            
            # التحقق من أن التاريخ ليس في الماضي
            now = datetime.now(tz)
            if dt < now:
                return False, None, "❌ لا يمكن الحجز في الماضي! الرجاء اختيار تاريخ ووقت مستقبلي"
            
            # التحقق من أن التاريخ ليس بعيداً جداً (مثلاً أكثر من سنة)
            if dt > now + timedelta(days=365):
                return False, None, "❌ التاريخ بعيد جداً! الحد الأقصى سنة واحدة"
            
            return True, dt, None
            
        except ValueError as e:
            return False, None, f"❌ صيغة التاريخ أو الوقت غير صحيحة. استخدم:\nالتاريخ: YYYY-MM-DD (مثال: 2026-02-15)\nالوقت: HH:MM (مثال: 14:30)"
    
    @staticmethod
    def validate_booking_type(booking_type: str) -> Tuple[bool, Optional[str]]:
        """التحقق من نوع الحجز"""
        valid_types = ['building', 'research', 'training']
        if booking_type not in valid_types:
            return False, f"❌ نوع حجز غير صحيح. الأنواع المتاحة: {', '.join(valid_types)}"
        return True, None
    
    @staticmethod
    def validate_details(details: str) -> Tuple[bool, Optional[str]]:
        """التحقق من التفاصيل"""
        if details and len(details) > 500:
            return False, "❌ التفاصيل طويلة جداً (الحد الأقصى 500 حرف)"
        return True, None

validators = Validators()


def validate_player_id(player_id: str):
    return validators.validate_player_id(player_id)


def validate_player_name(name: str):
    return validators.validate_player_name(name)


def validate_alliance_name(name: str):
    return validators.validate_alliance_name(name)


def validate_alliance_tag(tag: str):
    return validators.validate_alliance_tag(tag)


def validate_datetime(date_str: str, time_str: str):
    return validators.validate_datetime(date_str, time_str)


def validate_booking_type(booking_type: str):
    return validators.validate_booking_type(booking_type)


def validate_details(details: str):
    return validators.validate_details(details)
