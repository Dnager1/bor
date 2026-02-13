"""
نظام الحجوزات - Bookings Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import logging

from database import db
from database.models import Booking
from utils import validators, embeds, datetime_helper, permissions
from config import config

logger = logging.getLogger('bookings')

class BookingModal(discord.ui.Modal, title='📝 إنشاء حجز جديد'):
    """نموذج إدخال بيانات الحجز"""
    
    player_name = discord.ui.TextInput(
        label='اسم اللاعب',
        placeholder='أدخل اسم اللاعب...',
        required=True,
        max_length=50
    )
    
    player_id = discord.ui.TextInput(
        label='معرف اللاعب (Player ID)',
        placeholder='مثال: 12345678',
        required=True,
        max_length=15
    )
    
    alliance_name = discord.ui.TextInput(
        label='اسم التحالف',
        placeholder='أدخل اسم التحالف...',
        required=True,
        max_length=50
    )
    
    date = discord.ui.TextInput(
        label='التاريخ (YYYY-MM-DD)',
        placeholder='مثال: 2026-02-15',
        required=True,
        max_length=10
    )
    
    time = discord.ui.TextInput(
        label='الوقت (HH:MM)',
        placeholder='مثال: 14:30',
        required=True,
        max_length=5
    )
    
    details = discord.ui.TextInput(
        label='تفاصيل إضافية (اختياري)',
        placeholder='أضف أي ملاحظات...',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    def __init__(self, booking_type: str, cog):
        super().__init__()
        self.booking_type = booking_type
        self.cog = cog
    
    async def on_submit(self, interaction: discord.Interaction):
        """عند إرسال النموذج"""
        await interaction.response.defer(ephemeral=True)
        
        # التحقق من البيانات
        valid, error = validators.validate_player_name(self.player_name.value)
        if not valid:
            await interaction.followup.send(embed=embeds.create_error_embed("خطأ", error), ephemeral=True)
            return
        
        valid, error = validators.validate_player_id(self.player_id.value)
        if not valid:
            await interaction.followup.send(embed=embeds.create_error_embed("خطأ", error), ephemeral=True)
            return
        
        valid, error = validators.validate_alliance_name(self.alliance_name.value)
        if not valid:
            await interaction.followup.send(embed=embeds.create_error_embed("خطأ", error), ephemeral=True)
            return
        
        valid, dt, error = validators.validate_datetime(self.date.value, self.time.value)
        if not valid:
            await interaction.followup.send(embed=embeds.create_error_embed("خطأ", error), ephemeral=True)
            return
        
        # الحصول على المستخدم أو إنشاؤه
        user = await db.get_or_create_user(
            str(interaction.user.id),
            interaction.user.name,
            self.player_id.value
        )
        
        # التحقق من الحد الأقصى للحجوزات النشطة
        active_count = await db.get_active_bookings_count(user.user_id)
        if active_count >= config.MAX_ACTIVE_BOOKINGS:
            await interaction.followup.send(
                embed=embeds.create_error_embed(
                    "تجاوز الحد الأقصى",
                    f"لديك {active_count} حجوزات نشطة. الحد الأقصى هو {config.MAX_ACTIVE_BOOKINGS}.\n"
                    f"الرجاء إلغاء بعض الحجوزات أو إكمالها قبل إضافة حجوزات جديدة."
                ),
                ephemeral=True
            )
            return
        
        # التحقق من التعارضات
        has_conflict = await db.check_booking_conflict(user.user_id, dt)
        if has_conflict:
            await interaction.followup.send(
                embed=embeds.create_warning_embed(
                    "تعارض في المواعيد",
                    f"لديك حجز آخر في نفس الوقت: {dt}\n"
                    "لا يمكن حجز نفس الموعد مرتين."
                ),
                ephemeral=True
            )
            return
        
        # إنشاء الحجز
        booking = Booking(
            user_id=user.user_id,
            booking_type=self.booking_type,
            player_name=self.player_name.value,
            player_id=self.player_id.value,
            alliance_name=self.alliance_name.value,
            scheduled_time=dt,
            details=self.details.value if self.details.value else '',
            created_by=str(interaction.user.id)
        )
        
        booking_id = await db.create_booking(booking)
        booking.booking_id = booking_id
        
        # تسجيل العملية
        await db.log_action(
            'booking_created',
            f"تم إنشاء حجز جديد من نوع {self.booking_type}",
            str(interaction.user.id),
            booking_id,
            f"اللاعب: {self.player_name.value}, الموعد: {dt}"
        )
        
        logger.info(f"حجز جديد #{booking_id} - {interaction.user.name} - {self.booking_type}")
        
        # إرسال رسالة النجاح
        await interaction.followup.send(
            embed=embeds.create_booking_embed(booking),
            ephemeral=True
        )

class BookingTypeSelect(discord.ui.Select):
    """قائمة اختيار نوع الحجز"""
    
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(
                label='البناء',
                description='حجز موعد للبناء',
                emoji='🏗️',
                value='building'
            ),
            discord.SelectOption(
                label='الأبحاث',
                description='حجز موعد للأبحاث',
                emoji='🔬',
                value='research'
            ),
            discord.SelectOption(
                label='التدريب',
                description='حجز موعد للتدريب',
                emoji='⚔️',
                value='training'
            )
        ]
        
        super().__init__(
            placeholder='اختر نوع الحجز...',
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        """عند اختيار نوع الحجز"""
        booking_type = self.values[0]
        modal = BookingModal(booking_type, self.cog)
        await interaction.response.send_modal(modal)

class BookingTypeView(discord.ui.View):
    """عرض اختيار نوع الحجز"""
    
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.add_item(BookingTypeSelect(cog))

class BookingActionButtons(discord.ui.View):
    """أزرار إدارة الحجز"""
    
    def __init__(self, booking_id: int, user_id: str):
        super().__init__(timeout=300)
        self.booking_id = booking_id
        self.user_id = user_id
    
    @discord.ui.button(label='إلغاء الحجز', style=discord.ButtonStyle.danger, emoji='❌')
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إلغاء الحجز"""
        # التحقق من الصلاحيات
        if not permissions.can_manage_booking(interaction.user, self.user_id):
            await interaction.response.send_message(
                embed=embeds.create_error_embed("خطأ", "ليس لديك صلاحية لإلغاء هذا الحجز"),
                ephemeral=True
            )
            return
        
        # إلغاء الحجز
        await db.cancel_booking(self.booking_id, "تم الإلغاء بواسطة المستخدم")
        
        # تحديث النقاط
        booking = await db.get_booking(self.booking_id)
        if booking:
            await db.update_user_points(booking.user_id, config.POINTS_CANCELLED)
            await db.update_user_stats(booking.user_id, 'cancelled')
        
        await db.log_action(
            'booking_cancelled',
            f"تم إلغاء الحجز #{self.booking_id}",
            str(interaction.user.id),
            self.booking_id
        )
        
        await interaction.response.send_message(
            embed=embeds.create_success_embed("تم الإلغاء", f"تم إلغاء الحجز #{self.booking_id} بنجاح"),
            ephemeral=True
        )
        
        # تعطيل الأزرار
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

class BookingsCog(commands.Cog):
    """نظام الحجوزات"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='حجز', description='📝 إنشاء حجز جديد')
    async def book(self, interaction: discord.Interaction):
        """إنشاء حجز جديد"""
        view = BookingTypeView(self)
        embed = embeds.create_info_embed(
            "إنشاء حجز جديد",
            "اختر نوع الحجز من القائمة أدناه:\n\n"
            "🏗️ **البناء** - حجز موعد للبناء\n"
            "🔬 **الأبحاث** - حجز موعد للأبحاث\n"
            "⚔️ **التدريب** - حجز موعد للتدريب"
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name='مواعيدي', description='📅 عرض حجوزاتك')
    async def my_bookings(self, interaction: discord.Interaction):
        """عرض حجوزات المستخدم"""
        await interaction.response.defer(ephemeral=True)
        
        user = await db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.followup.send(
                embed=embeds.create_info_embed("لا توجد بيانات", "ليس لديك أي حجوزات بعد."),
                ephemeral=True
            )
            return
        
        bookings = await db.get_user_bookings(user.user_id, 'active')
        
        if not bookings:
            await interaction.followup.send(
                embed=embeds.create_info_embed("لا توجد حجوزات", "ليس لديك حجوزات نشطة حالياً."),
                ephemeral=True
            )
            return
        
        embed = embeds.create_bookings_list_embed(
            bookings,
            f"📅 حجوزاتك النشطة ({len(bookings)})"
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name='إلغاء', description='❌ إلغاء حجز')
    @app_commands.describe(booking_id='رقم الحجز المراد إلغاؤه')
    async def cancel(self, interaction: discord.Interaction, booking_id: int):
        """إلغاء حجز"""
        await interaction.response.defer(ephemeral=True)
        
        booking = await db.get_booking(booking_id)
        if not booking:
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", f"لم يتم العثور على الحجز #{booking_id}"),
                ephemeral=True
            )
            return
        
        # التحقق من الصلاحيات
        if not permissions.can_manage_booking(interaction.user, booking.created_by):
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "ليس لديك صلاحية لإلغاء هذا الحجز"),
                ephemeral=True
            )
            return
        
        if booking.status != 'active':
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "هذا الحجز غير نشط"),
                ephemeral=True
            )
            return
        
        # إلغاء الحجز
        await db.cancel_booking(booking_id, "تم الإلغاء بواسطة المستخدم")
        await db.update_user_points(booking.user_id, config.POINTS_CANCELLED)
        await db.update_user_stats(booking.user_id, 'cancelled')
        
        await db.log_action(
            'booking_cancelled',
            f"تم إلغاء الحجز #{booking_id}",
            str(interaction.user.id),
            booking_id
        )
        
        logger.info(f"تم إلغاء الحجز #{booking_id} بواسطة {interaction.user.name}")
        
        await interaction.followup.send(
            embed=embeds.create_success_embed("تم الإلغاء", f"تم إلغاء الحجز #{booking_id} بنجاح"),
            ephemeral=True
        )
    
    @app_commands.command(name='جدول', description='📊 عرض جدول المواعيد')
    @app_commands.describe(نوع='نوع الحجز: building, research, training')
    @app_commands.choices(نوع=[
        app_commands.Choice(name='🏗️ البناء', value='building'),
        app_commands.Choice(name='🔬 الأبحاث', value='research'),
        app_commands.Choice(name='⚔️ التدريب', value='training'),
        app_commands.Choice(name='📅 الكل', value='all')
    ])
    async def schedule(self, interaction: discord.Interaction, نوع: str = 'all'):
        """عرض جدول المواعيد"""
        await interaction.response.defer()
        
        if نوع == 'all':
            bookings = await db.get_all_active_bookings()
            title = "📊 جدول المواعيد - الكل"
        else:
            bookings = await db.get_bookings_by_type(نوع, 'active')
            booking_info = config.BOOKING_TYPES.get(نوع, {})
            emoji = booking_info.get('emoji', '📅')
            name = booking_info.get('name', نوع)
            title = f"{emoji} جدول المواعيد - {name}"
        
        if not bookings:
            await interaction.followup.send(
                embed=embeds.create_info_embed("لا توجد مواعيد", "لا توجد حجوزات نشطة حالياً.")
            )
            return
        
        embed = embeds.create_bookings_list_embed(bookings, title)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(BookingsCog(bot))
