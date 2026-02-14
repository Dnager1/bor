"""
نظام التحقق المحسّن - Enhanced Validators
Complete validation with bilingual error messages
"""
from datetime import datetime, timedelta
from typing import Tuple, Optional
import re
import pytz
from config import config


class EnhancedValidators:
    """Enhanced validators with better error messages"""
    
    @staticmethod
    def validate_datetime(date_str: str, time_str: str) -> Tuple[bool, Optional[datetime], str]:
        """
        Validate and parse date and time
        
        Returns:
            Tuple of (is_valid, datetime_object, error_message)
        """
        try:
            # Check date format
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return False, None, "❌ تنسيق التاريخ خاطئ. استخدم YYYY-MM-DD\nInvalid date format. Use YYYY-MM-DD"
            
            # Check time format
            if not re.match(r'^\d{2}:\d{2}$', time_str):
                return False, None, "❌ تنسيق الوقت خاطئ. استخدم HH:MM\nInvalid time format. Use HH:MM"
            
            # Parse datetime
            datetime_str = f"{date_str} {time_str}"
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            
            # Make timezone aware
            tz = pytz.timezone(config.TIMEZONE)
            dt = tz.localize(dt)
            
            # Check if in the past
            now = datetime.now(tz)
            if dt < now:
                return False, None, "❌ لا يمكن حجز موعد في الماضي\nCannot book in the past"
            
            # Check if too far in future
            max_future = now + timedelta(days=365)
            if dt > max_future:
                return False, None, "❌ لا يمكن الحجز لأكثر من سنة مقدماً\nCannot book more than 1 year ahead"
            
            return True, dt, ""
            
        except ValueError as e:
            return False, None, f"❌ تاريخ أو وقت غير صالح\nInvalid date or time: {str(e)}"
    
    @staticmethod
    def validate_duration(duration_str: str) -> Tuple[bool, int, str]:
        """Validate duration in days"""
        try:
            duration = int(duration_str)
            
            if duration < 1:
                return False, 0, "❌ المدة يجب أن تكون على الأقل يوم واحد\nDuration must be at least 1 day"
            
            if duration > 365:
                return False, 0, "❌ المدة لا يمكن أن تتجاوز 365 يوم\nDuration cannot exceed 365 days"
            
            return True, duration, ""
            
        except ValueError:
            return False, 0, "❌ المدة يجب أن تكون رقماً صحيحاً\nDuration must be a valid number"
    
    @staticmethod
    def validate_player_name(name: str) -> Tuple[bool, str]:
        """Validate player name"""
        name = name.strip()
        
        if not name:
            return False, "❌ اسم اللاعب مطلوب\nPlayer name is required"
        
        if len(name) > 100:
            return False, "❌ اسم اللاعب طويل جداً (الحد الأقصى 100 حرف)\nPlayer name too long (max 100 chars)"
        
        # Check for invalid characters
        if not re.match(r'^[\w\s\u0600-\u06FF\u0750-\u077F-]+$', name):
            return False, "❌ اسم اللاعب يحتوي على رموز غير صالحة\nPlayer name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def validate_alliance_name(name: str) -> Tuple[bool, str]:
        """Validate alliance name"""
        name = name.strip()
        
        if not name:
            return False, "❌ اسم التحالف مطلوب\nAlliance name is required"
        
        if len(name) < 3:
            return False, "❌ اسم التحالف قصير جداً (الحد الأدنى 3 أحرف)\nAlliance name too short (min 3 chars)"
        
        if len(name) > 50:
            return False, "❌ اسم التحالف طويل جداً (الحد الأقصى 50 حرف)\nAlliance name too long (max 50 chars)"
        
        return True, ""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        return text


# Export
__all__ = ['EnhancedValidators']
