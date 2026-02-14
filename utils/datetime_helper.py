"""
مساعد التاريخ والوقت - DateTime Helper
"""
from datetime import datetime, timedelta
from typing import Optional
import pytz
from config import config

class DateTimeHelper:
    """مساعد التاريخ والوقت"""
    
    @staticmethod
    def get_timezone():
        """Get configured timezone"""
        return pytz.timezone(config.TIMEZONE)
    
    @staticmethod
    def get_now() -> datetime:
        """الحصول على الوقت الحالي"""
        tz = pytz.timezone(config.TIMEZONE)
        return datetime.now(tz)
    
    @staticmethod
    def parse_datetime(date_str: str, time_str: str) -> Optional[datetime]:
        """تحليل التاريخ والوقت"""
        try:
            datetime_str = f"{date_str} {time_str}"
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            tz = pytz.timezone(config.TIMEZONE)
            return tz.localize(dt)
        except:
            return None
    
    @staticmethod
    def is_past(dt: datetime) -> bool:
        """التحقق من أن الوقت في الماضي"""
        now = DateTimeHelper.get_now()
        if dt.tzinfo is None:
            tz = pytz.timezone(config.TIMEZONE)
            dt = tz.localize(dt)
        return dt < now
    
    @staticmethod
    def get_time_until(dt: datetime) -> timedelta:
        """الحصول على الوقت المتبقي"""
        now = DateTimeHelper.get_now()
        if dt.tzinfo is None:
            tz = pytz.timezone(config.TIMEZONE)
            dt = tz.localize(dt)
        return dt - now
    
    @staticmethod
    def should_send_24h_reminder(booking) -> bool:
        """التحقق من إرسال تذكير 24 ساعة"""
        if not config.REMINDER_24H or booking.reminder_24h_sent:
            return False
        
        time_until = DateTimeHelper.get_time_until(booking.scheduled_time)
        # إرسال إذا كان الوقت المتبقي بين 23-25 ساعة
        return timedelta(hours=23) <= time_until <= timedelta(hours=25)
    
    @staticmethod
    def should_send_1h_reminder(booking) -> bool:
        """التحقق من إرسال تذكير ساعة واحدة"""
        if not config.REMINDER_1H or booking.reminder_1h_sent:
            return False
        
        time_until = DateTimeHelper.get_time_until(booking.scheduled_time)
        # إرسال إذا كان الوقت المتبقي بين 55-65 دقيقة
        return timedelta(minutes=55) <= time_until <= timedelta(minutes=65)
    
    @staticmethod
    def should_send_now_reminder(booking) -> bool:
        """التحقق من إرسال تذكير الآن"""
        if not config.REMINDER_NOW or booking.reminder_now_sent:
            return False
        
        time_until = DateTimeHelper.get_time_until(booking.scheduled_time)
        # إرسال إذا كان الوقت المتبقي بين -5 و +5 دقائق
        return timedelta(minutes=-5) <= time_until <= timedelta(minutes=5)
    
    @staticmethod
    def get_today_range() -> tuple:
        """الحصول على نطاق اليوم"""
        now = DateTimeHelper.get_now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end
    
    @staticmethod
    def get_week_range() -> tuple:
        """الحصول على نطاق الأسبوع"""
        now = DateTimeHelper.get_now()
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end

datetime_helper = DateTimeHelper()

# Module-level convenience functions
def get_timezone():
    """Get configured timezone"""
    return DateTimeHelper.get_timezone()

def get_now():
    """Get current time with timezone"""
    return DateTimeHelper.get_now()

def is_past(dt):
    """Check if datetime is in the past"""
    return DateTimeHelper.is_past(dt)

def get_time_until(dt):
    """Get time remaining until datetime"""
    return DateTimeHelper.get_time_until(dt)
