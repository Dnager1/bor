"""
أدوات إنشاء الـ Embeds - Discord Embeds Helper
"""
import discord
from datetime import datetime
from typing import List, Optional
from config import config
from database.models import Booking, User, Alliance

class EmbedBuilder:
    """أداة إنشاء الـ Embeds"""
    
    @staticmethod
    def create_booking_embed(booking: Booking, user: Optional[User] = None) -> discord.Embed:
        """إنشاء embed للحجز"""
        booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
        color = booking_info.get('color', 0x3498db)
        emoji = booking_info.get('emoji', '📅')
        type_name = booking_info.get('name', booking.booking_type)
        
        embed = discord.Embed(
            title=f"{emoji} حجز {type_name}",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👤 اسم اللاعب", value=booking.player_name, inline=True)
        embed.add_field(name="🆔 معرف اللاعب", value=booking.player_id, inline=True)
        embed.add_field(name="🏰 التحالف", value=booking.alliance_name, inline=True)
        
        # الموعد
        from utils.formatters import formatters
        embed.add_field(
            name="⏰ موعد الحجز", 
            value=formatters.format_datetime(booking.scheduled_time), 
            inline=False
        )
        
        # الوقت المتبقي
        embed.add_field(
            name="⏳ الوقت المتبقي",
            value=formatters.format_time_remaining(booking.scheduled_time),
            inline=False
        )
        
        # التفاصيل
        if booking.details:
            embed.add_field(name="📝 التفاصيل", value=booking.details, inline=False)
        
        # الحالة
        status_emoji = {
            'active': '🟢 نشط',
            'completed': '✅ مكتمل',
            'cancelled': '❌ ملغي',
            'expired': '⏰ منتهي'
        }
        embed.add_field(
            name="📋 الحالة", 
            value=status_emoji.get(booking.status, booking.status), 
            inline=True
        )
        
        # معرف الحجز
        embed.add_field(name="🔢 رقم الحجز", value=f"#{booking.booking_id}", inline=True)
        
        embed.set_footer(text=f"بوت مواعيد النجاة في الصقيع")
        
        return embed
    
    @staticmethod
    def create_bookings_list_embed(bookings: List[Booking], title: str, page: int = 1, per_page: int = 5) -> discord.Embed:
        """إنشاء embed لقائمة الحجوزات"""
        embed = discord.Embed(
            title=title,
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        if not bookings:
            embed.description = "📭 لا توجد حجوزات"
            return embed
        
        total = len(bookings)
        total_pages = (total + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        
        start = (page - 1) * per_page
        end = start + per_page
        page_bookings = bookings[start:end]
        
        from utils.formatters import formatters
        
        for booking in page_bookings:
            booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
            emoji = booking_info.get('emoji', '📅')
            type_name = booking_info.get('name', booking.booking_type)
            
            value = f"👤 {booking.player_name} | 🆔 {booking.player_id}\n"
            value += f"🏰 {booking.alliance_name}\n"
            value += f"⏰ {formatters.format_datetime(booking.scheduled_time)}\n"
            value += f"⏳ {formatters.format_time_remaining(booking.scheduled_time)}"
            
            embed.add_field(
                name=f"{emoji} {type_name} - #{booking.booking_id}",
                value=value,
                inline=False
            )
        
        if total_pages > 1:
            embed.set_footer(text=f"صفحة {page}/{total_pages} | المجموع: {total}")
        else:
            embed.set_footer(text=f"المجموع: {total}")
        
        return embed
    
    @staticmethod
    def create_stats_embed(user: User) -> discord.Embed:
        """إنشاء embed للإحصائيات"""
        embed = discord.Embed(
            title="📊 إحصائياتك",
            color=0x2ecc71,
            timestamp=datetime.now()
        )
        
        completion_rate = 0
        if user.total_bookings > 0:
            completion_rate = (user.completed_bookings / user.total_bookings) * 100
        
        embed.add_field(name="⭐ النقاط", value=f"**{user.points}**", inline=True)
        embed.add_field(name="📅 إجمالي الحجوزات", value=f"**{user.total_bookings}**", inline=True)
        embed.add_field(name="✅ المكتملة", value=f"**{user.completed_bookings}**", inline=True)
        embed.add_field(name="❌ الملغاة", value=f"**{user.cancelled_bookings}**", inline=True)
        embed.add_field(name="📈 معدل الإنجاز", value=f"**{completion_rate:.1f}%**", inline=True)
        embed.add_field(name="🆔 معرف اللاعب", value=f"`{user.player_id}`", inline=True)
        
        embed.set_footer(text=f"المستخدم: {user.username}")
        
        return embed
    
    @staticmethod
    def create_leaderboard_embed(users: List[User], title: str = "🏆 لوحة المتصدرين") -> discord.Embed:
        """إنشاء embed للوحة المتصدرين"""
        embed = discord.Embed(
            title=title,
            color=0xf39c12,
            timestamp=datetime.now()
        )
        
        medals = ['🥇', '🥈', '🥉']
        description = ""
        
        for i, user in enumerate(users, 1):
            medal = medals[i-1] if i <= 3 else f"`{i}.`"
            description += f"{medal} **{user.username}**\n"
            description += f"   ⭐ {user.points} نقطة | ✅ {user.completed_bookings} منجز\n\n"
        
        embed.description = description
        embed.set_footer(text="أفضل اللاعبين في النجاة في الصقيع")
        
        return embed
    
    @staticmethod
    def create_admin_stats_embed(stats: dict) -> discord.Embed:
        """إنشاء embed لإحصائيات الإدارة"""
        embed = discord.Embed(
            title="📊 إحصائيات البوت",
            color=0xe74c3c,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📅 الحجوزات",
            value=f"المجموع: **{stats['total_bookings']}**\n"
                  f"النشطة: **{stats['active_bookings']}**\n"
                  f"المكتملة: **{stats['completed_bookings']}**",
            inline=True
        )
        
        embed.add_field(
            name="👥 المستخدمون",
            value=f"المجموع: **{stats['total_users']}**",
            inline=True
        )
        
        embed.add_field(
            name="🏰 التحالفات",
            value=f"المجموع: **{stats['total_alliances']}**",
            inline=True
        )
        
        embed.set_footer(text="إحصائيات شاملة للبوت")
        
        return embed
    
    @staticmethod
    def create_success_embed(title: str, description: str) -> discord.Embed:
        """إنشاء embed للنجاح"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=0x2ecc71,
            timestamp=datetime.now()
        )
        return embed
    
    @staticmethod
    def create_error_embed(title: str, description: str) -> discord.Embed:
        """إنشاء embed للخطأ"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=0xe74c3c,
            timestamp=datetime.now()
        )
        return embed
    
    @staticmethod
    def create_info_embed(title: str, description: str) -> discord.Embed:
        """إنشاء embed للمعلومات"""
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=0x3498db,
            timestamp=datetime.now()
        )
        return embed
    
    @staticmethod
    def create_warning_embed(title: str, description: str) -> discord.Embed:
        """إنشاء embed للتحذير"""
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=0xf39c12,
            timestamp=datetime.now()
        )
        return embed

embeds = EmbedBuilder()
