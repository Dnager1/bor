"""
نظام الأزرار التفاعلية - Interactive Buttons System
"""
import discord
from discord import ui
from typing import Optional, Callable, List
import logging
from datetime import datetime

logger = logging.getLogger('buttons')

class MenuButton(ui.Button):
    """زر مخصص مع callback"""
    def __init__(self, label: str, emoji: Optional[str] = None, style: discord.ButtonStyle = discord.ButtonStyle.primary, callback_func: Optional[Callable] = None, **kwargs):
        super().__init__(label=label, emoji=emoji, style=style, **kwargs)
        self.callback_func = callback_func
    
    async def callback(self, interaction: discord.Interaction):
        if self.callback_func:
            await self.callback_func(interaction)

class MainMenuView(ui.View):
    """القائمة الرئيسية بالأزرار"""
    def __init__(self):
        super().__init__(timeout=None)
        
        # زر إنشاء حجز جديد
        self.add_item(MenuButton(
            label="حجز جديد",
            emoji="📝",
            style=discord.ButtonStyle.success,
            custom_id="btn_new_booking",
            callback_func=self.new_booking_callback
        ))
        
        # زر عرض حجوزاتي
        self.add_item(MenuButton(
            label="حجوزاتي",
            emoji="📋",
            style=discord.ButtonStyle.primary,
            custom_id="btn_my_bookings",
            callback_func=self.my_bookings_callback
        ))
        
        # زر الإحصائيات
        self.add_item(MenuButton(
            label="إحصائياتي",
            emoji="📊",
            style=discord.ButtonStyle.secondary,
            custom_id="btn_my_stats",
            callback_func=self.my_stats_callback
        ))
        
        # زر التحالفات
        self.add_item(MenuButton(
            label="التحالفات",
            emoji="🏰",
            style=discord.ButtonStyle.secondary,
            custom_id="btn_alliances",
            callback_func=self.alliances_callback
        ))
        
        # زر المساعدة
        self.add_item(MenuButton(
            label="المساعدة",
            emoji="❓",
            style=discord.ButtonStyle.secondary,
            custom_id="btn_help",
            callback_func=self.help_callback
        ))
    
    async def new_booking_callback(self, interaction: discord.Interaction):
        """إنشاء حجز جديد"""
        view = BookingTypeSelectView()
        embed = discord.Embed(
            title="📝 حجز موعد جديد",
            description="اختر نوع الموعد الذي تريد حجزه:",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def my_bookings_callback(self, interaction: discord.Interaction):
        """عرض حجوزاتي"""
        from database import db
        bookings = await db.get_user_bookings(str(interaction.user.id))
        
        if not bookings:
            await interaction.response.send_message("📭 ليس لديك أي حجوزات حالياً", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 حجوزاتي",
            description=f"لديك {len(bookings)} حجز نشط",
            color=discord.Color.blue()
        )
        
        for booking in bookings[:5]:  # أول 5 حجوزات
            status = "✅ منجز" if booking.status == "completed" else "⏳ قيد الانتظار"
            from config import config
            booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
            emoji = booking_info.get('emoji', '📅')
            name = booking_info.get('name', booking.booking_type)
            
            from utils.formatters import formatters
            date_str = formatters.format_datetime(booking.scheduled_time, include_time=True) if booking.scheduled_time else 'غير محدد'
            
            embed.add_field(
                name=f"{emoji} {name}",
                value=f"📅 {date_str}\n{status}",
                inline=False
            )
        
        view = BookingsActionsView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def my_stats_callback(self, interaction: discord.Interaction):
        """عرض إحصائياتي"""
        from database import db
        user = await db.get_or_create_user(str(interaction.user.id), interaction.user.name, "")
        
        embed = discord.Embed(
            title="📊 إحصائياتي",
            description=f"مرحباً {interaction.user.mention}",
            color=discord.Color.gold()
        )
        embed.add_field(name="⭐ النقاط", value=f"{user.points} نقطة", inline=True)
        embed.add_field(name="✅ حجوزات منجزة", value=str(user.completed_bookings), inline=True)
        embed.add_field(name="❌ حجوزات ملغاة", value=str(user.cancelled_bookings), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def alliances_callback(self, interaction: discord.Interaction):
        """التحالفات"""
        embed = discord.Embed(
            title="🏰 التحالفات",
            description="إدارة تحالفك ومشاهدة التحالفات المتاحة",
            color=discord.Color.purple()
        )
        view = AllianceMenuView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def help_callback(self, interaction: discord.Interaction):
        """المساعدة"""
        embed = discord.Embed(
            title="❓ المساعدة",
            description="**الأوامر المتاحة:**",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 الحجوزات",
            value="`/حجز` - إنشاء حجز جديد\n`/مواعيدي` - عرض حجوزاتي\n`/إلغاء` - إلغاء حجز",
            inline=False
        )
        embed.add_field(
            name="📊 الإحصائيات",
            value="`/mystats` - عرض نقاطي وإنجازاتي\n`/leaderboard` - أفضل اللاعبين",
            inline=False
        )
        embed.add_field(
            name="🏰 التحالفات",
            value="`/alliance info` - معلومات التحالف\n`/alliance join` - الانضمام لتحالف",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BookingTypeSelectView(ui.View):
    """اختيار نوع الحجز"""
    def __init__(self):
        super().__init__(timeout=300)
    
    @ui.button(label="البناء", emoji="🏗️", style=discord.ButtonStyle.primary, custom_id="booking_type_building")
    async def building_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_booking_type(interaction, "building")
    
    @ui.button(label="الأبحاث", emoji="🔬", style=discord.ButtonStyle.primary, custom_id="booking_type_research")
    async def research_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_booking_type(interaction, "research")
    
    @ui.button(label="التدريب", emoji="⚔️", style=discord.ButtonStyle.primary, custom_id="booking_type_training")
    async def training_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_booking_type(interaction, "training")
    
    async def handle_booking_type(self, interaction: discord.Interaction, booking_type: str):
        """معالجة اختيار نوع الحجز"""
        # فتح Modal لإدخال تفاصيل الحجز
        modal = BookingDetailsModal(booking_type)
        await interaction.response.send_modal(modal)

class BookingDetailsModal(ui.Modal, title="تفاصيل الحجز"):
    """نموذج إدخال تفاصيل الحجز"""
    def __init__(self, booking_type: str):
        super().__init__()
        self.booking_type = booking_type
    
    date_input = ui.TextInput(
        label="تاريخ الموعد (YYYY-MM-DD)",
        placeholder="مثال: 2026-02-20",
        required=True,
        max_length=10
    )
    
    time_input = ui.TextInput(
        label="وقت الموعد (HH:MM)",
        placeholder="مثال: 14:30",
        required=True,
        max_length=5
    )
    
    player_id_input = ui.TextInput(
        label="رقم اللاعب",
        placeholder="مثال: 12345678",
        required=True,
        max_length=10
    )
    
    notes_input = ui.TextInput(
        label="ملاحظات (اختياري)",
        placeholder="أي معلومات إضافية",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """عند إرسال النموذج"""
        from database import db
        from utils import validators
        from utils.datetime_helper import parse_datetime
        
        # التحقق من البيانات
        date_str = self.date_input.value.strip()
        time_str = self.time_input.value.strip()
        player_id = self.player_id_input.value.strip()
        notes = self.notes_input.value.strip() if self.notes_input.value else ""
        
        # التحقق من صيغة رقم اللاعب
        is_valid, error = validators.validate_player_id(player_id)
        if not is_valid:
            await interaction.response.send_message(f"❌ {error}", ephemeral=True)
            return
        
        # التحقق من التاريخ والوقت
        try:
            scheduled_datetime = parse_datetime(date_str, time_str)
        except Exception as e:
            await interaction.response.send_message(f"❌ صيغة التاريخ أو الوقت غير صحيحة: {e}", ephemeral=True)
            return
        
        # إنشاء الحجز
        try:
            user = await db.get_or_create_user(
                str(interaction.user.id),
                interaction.user.name,
                player_id
            )

            from database.models import Booking
            booking = Booking(
                user_id=user.user_id,
                booking_type=self.booking_type,
                player_name=interaction.user.name,
                player_id=player_id,
                alliance_name="",
                scheduled_time=scheduled_datetime,
                details=notes,
                created_by=str(interaction.user.id),
                duration_days=1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            booking_id = await db.create_booking(booking)
            
            from config import config
            booking_info = config.BOOKING_TYPES.get(self.booking_type, {})
            emoji = booking_info.get('emoji', '📅')
            name = booking_info.get('name', self.booking_type)
            
            embed = discord.Embed(
                title="✅ تم إنشاء الحجز بنجاح",
                description=f"تم حجز موعد {name}",
                color=discord.Color.green()
            )
            embed.add_field(name="📅 التاريخ", value=date_str, inline=True)
            embed.add_field(name="⏰ الوقت", value=time_str, inline=True)
            embed.add_field(name="🆔 رقم اللاعب", value=player_id, inline=True)
            if notes:
                embed.add_field(name="📝 ملاحظات", value=notes, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"فشل إنشاء الحجز: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ فشل إنشاء الحجز: {e}", ephemeral=True)

class BookingsActionsView(ui.View):
    """أزرار إجراءات الحجوزات"""
    def __init__(self):
        super().__init__(timeout=300)
    
    @ui.button(label="🔄 تحديث", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: ui.Button):
        # إعادة تحميل الحجوزات
        await interaction.response.send_message("🔄 جاري التحديث...", ephemeral=True)
    
    @ui.button(label="❌ إلغاء حجز", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        # فتح قائمة لاختيار الحجز للإلغاء
        await interaction.response.send_message("⚠️ استخدم `/إلغاء` لإلغاء حجز معين", ephemeral=True)

class AllianceMenuView(ui.View):
    """قائمة التحالفات"""
    def __init__(self):
        super().__init__(timeout=300)
    
    @ui.button(label="🏰 تحالفي", style=discord.ButtonStyle.primary)
    async def my_alliance_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("🏰 معلومات تحالفك", ephemeral=True)
    
    @ui.button(label="➕ إنشاء تحالف", style=discord.ButtonStyle.success)
    async def create_alliance_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = CreateAllianceModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="🔍 تصفح التحالفات", style=discord.ButtonStyle.secondary)
    async def browse_alliances_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("🔍 التحالفات المتاحة", ephemeral=True)

class CreateAllianceModal(ui.Modal, title="إنشاء تحالف جديد"):
    """نموذج إنشاء تحالف"""
    
    name_input = ui.TextInput(
        label="اسم التحالف",
        placeholder="مثال: فرسان الشمال",
        required=True,
        max_length=50
    )
    
    tag_input = ui.TextInput(
        label="رمز التحالف",
        placeholder="مثال: KON",
        required=True,
        min_length=3,
        max_length=3
    )
    
    description_input = ui.TextInput(
        label="وصف التحالف",
        placeholder="وصف مختصر للتحالف",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """عند إرسال النموذج"""
        from database import db
        
        try:
            leader = await db.get_or_create_user(
                str(interaction.user.id),
                interaction.user.name,
                str(interaction.user.id)
            )

            alliance_id = await db.create_alliance(
                name=self.name_input.value.strip(),
                tag=self.tag_input.value.strip().upper(),
                leader_id=leader.user_id,
                description=self.description_input.value.strip() if self.description_input.value else ""
            )

            alliance = await db.get_alliance(alliance_id)
            
            embed = discord.Embed(
                title="✅ تم إنشاء التحالف بنجاح",
                description=f"**{alliance.name}** [{alliance.tag}]" if alliance else "تم إنشاء التحالف",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"فشل إنشاء التحالف: {e}", exc_info=True)
            await interaction.response.send_message(f"❌ فشل إنشاء التحالف: {e}", ephemeral=True)
