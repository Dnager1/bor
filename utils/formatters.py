"""
أدوات تنسيق الرسائل - Message Formatters
"""
from datetime import datetime
from typing import List
import pytz
from config import config
from database.models import Booking, User, Alliance

class Formatters:
    """أدوات تنسيق الرسائل"""
    
    @staticmethod
    def format_datetime(dt: datetime, include_time: bool = True) -> str:
        """تنسيق التاريخ والوقت"""
        if not dt:
            return "غير محدد"
        
        # تحويل إلى المنطقة الزمنية المحلية
        if dt.tzinfo is None:
            tz = pytz.timezone(config.TIMEZONE)
            dt = tz.localize(dt)
        else:
            dt = dt.astimezone(pytz.timezone(config.TIMEZONE))
        
        # أسماء الأيام بالعربية
        days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
        day_name = days[dt.weekday()]
        
        # أسماء الأشهر بالعربية
        months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        month_name = months[dt.month - 1]
        
        if include_time:
            return f"{day_name} {dt.day} {month_name} {dt.year} - {dt.strftime('%H:%M')}"
        else:
            return f"{day_name} {dt.day} {month_name} {dt.year}"
    
    @staticmethod
    def format_booking(booking: Booking) -> str:
        """تنسيق معلومات الحجز"""
        booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
        emoji = booking_info.get('emoji', '📅')
        type_name = booking_info.get('name', booking.booking_type)
        
        status_emoji = {
            'active': '🟢',
            'completed': '✅',
            'cancelled': '❌',
            'expired': '⏰'
        }
        
        text = f"{emoji} **{type_name}** {status_emoji.get(booking.status, '❓')}\n"
        text += f"┌─────────────────────────────┐\n"
        text += f"│ 👤 اللاعب: {booking.player_name}\n"
        text += f"│ 🆔 المعرف: {booking.player_id}\n"
        text += f"│ 🏰 التحالف: {booking.alliance_name}\n"
        text += f"│ ⏰ الموعد: {Formatters.format_datetime(booking.scheduled_time)}\n"
        
        if booking.details:
            text += f"│ 📝 التفاصيل: {booking.details}\n"
        
        text += f"│ 📋 الحالة: {Formatters.format_status(booking.status)}\n"
        text += f"└─────────────────────────────┘\n"
        
        return text
    
    @staticmethod
    def format_status(status: str) -> str:
        """تنسيق حالة الحجز"""
        status_map = {
            'active': 'نشط',
            'completed': 'مكتمل',
            'cancelled': 'ملغي',
            'expired': 'منتهي'
        }
        return status_map.get(status, status)
    
    @staticmethod
    def format_booking_list(bookings: List[Booking], page: int = 1, per_page: int = 5) -> str:
        """تنسيق قائمة الحجوزات"""
        if not bookings:
            return "📭 لا توجد حجوزات"
        
        total = len(bookings)
        total_pages = (total + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        
        start = (page - 1) * per_page
        end = start + per_page
        page_bookings = bookings[start:end]
        
        text = ""
        for booking in page_bookings:
            text += Formatters.format_booking(booking) + "\n"
        
        if total_pages > 1:
            text += f"\n📄 صفحة {page}/{total_pages} | المجموع: {total}\n"
        
        return text
    
    @staticmethod
    def format_user_stats(user: User) -> str:
        """تنسيق إحصائيات المستخدم"""
        completion_rate = 0
        if user.total_bookings > 0:
            completion_rate = (user.completed_bookings / user.total_bookings) * 100
        
        text = f"📊 **إحصائياتك**\n\n"
        text += f"⭐ النقاط: **{user.points}**\n"
        text += f"📅 إجمالي الحجوزات: **{user.total_bookings}**\n"
        text += f"✅ المكتملة: **{user.completed_bookings}**\n"
        text += f"❌ الملغاة: **{user.cancelled_bookings}**\n"
        text += f"📈 معدل الإنجاز: **{completion_rate:.1f}%**\n"
        
        return text
    
    @staticmethod
    def format_alliance_stats(alliance: Alliance) -> str:
        """تنسيق إحصائيات التحالف"""
        text = f"🏰 **{alliance.name}**\n\n"
        text += f"👥 الأعضاء: **{alliance.member_count}**\n"
        text += f"📅 الحجوزات: **{alliance.total_bookings}**\n"
        text += f"⭐ النقاط: **{alliance.total_points}**\n"
        
        if alliance.description:
            text += f"\n📝 {alliance.description}\n"
        
        return text
    
    @staticmethod
    def format_time_remaining(dt: datetime) -> str:
        """تنسيق الوقت المتبقي"""
        if not dt:
            return "غير محدد"
        
        now = datetime.now(pytz.timezone(config.TIMEZONE))
        if dt.tzinfo is None:
            dt = pytz.timezone(config.TIMEZONE).localize(dt)
        else:
            dt = dt.astimezone(pytz.timezone(config.TIMEZONE))
        
        delta = dt - now
        
        if delta.total_seconds() < 0:
            return "⏰ انتهى الموعد"
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"⏳ متبقي {days} يوم و {hours} ساعة"
        elif hours > 0:
            return f"⏳ متبقي {hours} ساعة و {minutes} دقيقة"
        else:
            return f"⏳ متبقي {minutes} دقيقة"
    
    @staticmethod
    def format_leaderboard(users: List[User], title: str = "🏆 لوحة المتصدرين") -> str:
        """تنسيق لوحة المتصدرين"""
        text = f"**{title}**\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        
        for i, user in enumerate(users, 1):
            medal = medals[i-1] if i <= 3 else f"`{i}.`"
            text += f"{medal} **{user.username}**\n"
            text += f"   ⭐ {user.points} نقطة | ✅ {user.completed_bookings} منجز\n"
        
        return text

formatters = Formatters()
