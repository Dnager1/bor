"""
نظام الحجوزات - Bookings Cog
Enhanced with action buttons for all interactions
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import logging

from database import db
from database.models import Booking
from utils import validators, embeds, datetime_helper, permissions
from utils.ui_components import create_colored_embed
from utils.translator import translator
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
    
    duration_days = discord.ui.TextInput(
        label='عدد الأيام | Days Count',
        placeholder='مثال: 3 (من 1 إلى 365 يوم)',
        required=True,
        max_length=3,
        default='1'
    )
    
    def __init__(self, booking_type: str, cog):
        super().__init__(title='📝 إنشاء حجز جديد')
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
        
        # التحقق من عدد الأيام
        try:
            duration = int(self.duration_days.value)
            if duration < 1 or duration > 365:
                await interaction.followup.send(
                    embed=embeds.create_error_embed(
                        "خطأ في عدد الأيام",
                        "يجب أن يكون عدد الأيام بين 1 و 365 يوماً"
                    ),
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.followup.send(
                embed=embeds.create_error_embed(
                    "خطأ في عدد الأيام",
                    "يجب إدخال رقم صحيح لعدد الأيام"
                ),
                ephemeral=True
            )
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
            duration_days=duration,
            details="",
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
            f"اللاعب: {self.player_name.value}, الموعد: {dt}, المدة: {duration} أيام"
        )
        
        logger.info(f"حجز جديد #{booking_id} - {interaction.user.name} - {self.booking_type} - {duration} أيام")
        
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
    
    @discord.ui.button(label='✅ إكمال', style=discord.ButtonStyle.success, emoji='✅', row=0)
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إكمال الحجز"""
        # التحقق من الصلاحيات
        if not permissions.can_manage_booking(interaction.user, self.user_id):
            await interaction.response.send_message(
                embed=create_colored_embed("خطأ", "ليس لديك صلاحية لإدارة هذا الحجز", 'error'),
                ephemeral=True
            )
            return
        
        # إكمال الحجز
        await db.complete_booking(self.booking_id)
        
        # تحديث النقاط
        booking = await db.get_booking(self.booking_id)
        if booking:
            await db.update_user_points(booking.user_id, config.POINTS_COMPLETED)
            await db.update_user_stats(booking.user_id, 'completed')
        
        await db.log_action(
            'booking_completed',
            f"تم إكمال الحجز #{self.booking_id}",
            str(interaction.user.id),
            self.booking_id
        )
        
        await interaction.response.send_message(
            embed=create_colored_embed("✅ تم الإكمال", f"تم إكمال الحجز #{self.booking_id} بنجاح!", 'success'),
            ephemeral=True
        )
        
        # تعطيل الأزرار
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
    
    @discord.ui.button(label='❌ إلغاء', style=discord.ButtonStyle.danger, emoji='❌', row=0)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إلغاء الحجز"""
        # التحقق من الصلاحيات
        if not permissions.can_manage_booking(interaction.user, self.user_id):
            await interaction.response.send_message(
                embed=create_colored_embed("خطأ", "ليس لديك صلاحية لإلغاء هذا الحجز", 'error'),
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
            embed=create_colored_embed("تم الإلغاء", f"تم إلغاء الحجز #{self.booking_id} بنجاح", 'success'),
            ephemeral=True
        )
        
        # تعطيل الأزرار
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

class BookingsListView(discord.ui.View):
    """عرض قائمة الحجوزات مع أزرار التنقل والإجراءات"""
    
    def __init__(self, bookings: list, user_id: str, title: str, page: int = 0):
        super().__init__(timeout=300)
        self.bookings = bookings
        self.user_id = user_id
        self.title = title
        self.page = page
        self.per_page = 3  # عرض 3 حجوزات في كل صفحة
        self.total_pages = (len(bookings) + self.per_page - 1) // self.per_page if bookings else 1
        
        self._update_buttons()
    
    def _update_buttons(self):
        """تحديث أزرار التنقل"""
        self.clear_items()
        
        # أزرار التنقل بين الصفحات
        if self.total_pages > 1:
            prev_button = discord.ui.Button(
                label="⬅️ السابق",
                style=discord.ButtonStyle.secondary,
                disabled=(self.page == 0),
                custom_id='prev_page'
            )
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
            
            page_button = discord.ui.Button(
                label=f"صفحة {self.page + 1}/{self.total_pages}",
                style=discord.ButtonStyle.secondary,
                disabled=True
            )
            self.add_item(page_button)
            
            next_button = discord.ui.Button(
                label="➡️ التالي",
                style=discord.ButtonStyle.secondary,
                disabled=(self.page >= self.total_pages - 1),
                custom_id='next_page'
            )
            next_button.callback = self.next_page
            self.add_item(next_button)
        
        # زر العودة للقائمة الرئيسية
        back_button = discord.ui.Button(
            label="🔙 القائمة الرئيسية",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        back_button.callback = self.back_to_menu
        self.add_item(back_button)
        
        # إضافة أزرار الإجراءات لكل حجز في الصفحة الحالية
        start = self.page * self.per_page
        end = min(start + self.per_page, len(self.bookings))
        page_bookings = self.bookings[start:end]
        
        for i, booking in enumerate(page_bookings):
            complete_btn = discord.ui.Button(
                label=f"✅ إكمال #{booking.booking_id}",
                style=discord.ButtonStyle.success,
                custom_id=f'complete_{booking.booking_id}',
                row=2 + i
            )
            complete_btn.callback = lambda inter, b=booking: self.complete_booking(inter, b)
            self.add_item(complete_btn)
            
            cancel_btn = discord.ui.Button(
                label=f"❌ إلغاء #{booking.booking_id}",
                style=discord.ButtonStyle.danger,
                custom_id=f'cancel_{booking.booking_id}',
                row=2 + i
            )
            cancel_btn.callback = lambda inter, b=booking: self.cancel_booking(inter, b)
            self.add_item(cancel_btn)
    
    async def complete_booking(self, interaction: discord.Interaction, booking):
        """إكمال حجز"""
        if not permissions.can_manage_booking(interaction.user, booking.created_by):
            await interaction.response.send_message(
                embed=create_colored_embed("خطأ", "ليس لديك صلاحية لإدارة هذا الحجز", 'error'),
                ephemeral=True
            )
            return
        
        await db.complete_booking(booking.booking_id)
        await db.update_user_points(booking.user_id, config.POINTS_COMPLETED)
        await db.update_user_stats(booking.user_id, 'completed')
        
        await interaction.response.send_message(
            embed=create_colored_embed("✅ تم الإكمال", f"تم إكمال الحجز #{booking.booking_id} بنجاح!", 'success'),
            ephemeral=True
        )
        
        # إعادة تحميل القائمة
        await self.refresh_list(interaction)
    
    async def cancel_booking(self, interaction: discord.Interaction, booking):
        """إلغاء حجز"""
        if not permissions.can_manage_booking(interaction.user, booking.created_by):
            await interaction.response.send_message(
                embed=create_colored_embed("خطأ", "ليس لديك صلاحية لإلغاء هذا الحجز", 'error'),
                ephemeral=True
            )
            return
        
        await db.cancel_booking(booking.booking_id, "تم الإلغاء بواسطة المستخدم")
        await db.update_user_points(booking.user_id, config.POINTS_CANCELLED)
        await db.update_user_stats(booking.user_id, 'cancelled')
        
        await interaction.response.send_message(
            embed=create_colored_embed("تم الإلغاء", f"تم إلغاء الحجز #{booking.booking_id}", 'success'),
            ephemeral=True
        )
        
        # إعادة تحميل القائمة
        await self.refresh_list(interaction)
    
    async def refresh_list(self, interaction: discord.Interaction):
        """إعادة تحميل قائمة الحجوزات"""
        # إعادة جلب الحجوزات النشطة
        user = await db.get_user_by_discord_id(self.user_id)
        if user:
            self.bookings = await db.get_user_bookings(user.user_id, 'active')
            self.total_pages = (len(self.bookings) + self.per_page - 1) // self.per_page if self.bookings else 1
            
            if self.page >= self.total_pages:
                self.page = max(0, self.total_pages - 1)
            
            self._update_buttons()
            
            embed = self.create_embed()
            await interaction.message.edit(embed=embed, view=self)
    
    async def prev_page(self, interaction: discord.Interaction):
        """الصفحة السابقة"""
        if self.page > 0:
            self.page -= 1
            self._update_buttons()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def next_page(self, interaction: discord.Interaction):
        """الصفحة التالية"""
        if self.page < self.total_pages - 1:
            self.page += 1
            self._update_buttons()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def back_to_menu(self, interaction: discord.Interaction):
        """العودة للقائمة الرئيسية"""
        from cogs.main_menu import MainMenuView
        from utils.translator import get_text
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(self.user_id, is_admin)
        
        embed = create_colored_embed(
            get_text(self.user_id, 'main_menu.title'),
            get_text(self.user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    def create_embed(self):
        """إنشاء embed للصفحة الحالية"""
        embed = discord.Embed(
            title=self.title,
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        if not self.bookings:
            embed.description = "📭 لا توجد حجوزات نشطة"
            return embed
        
        start = self.page * self.per_page
        end = min(start + self.per_page, len(self.bookings))
        page_bookings = self.bookings[start:end]
        
        from utils.formatters import formatters
        
        for booking in page_bookings:
            booking_info = config.BOOKING_TYPES.get(booking.booking_type, {})
            emoji = booking_info.get('emoji', '📅')
            type_name = booking_info.get('name', booking.booking_type)
            
            value = f"👤 {booking.player_name} | 🆔 {booking.player_id}\n"
            value += f"🏰 {booking.alliance_name}\n"
            value += f"⏰ {formatters.format_datetime(booking.scheduled_time)}\n"
            value += f"📅 المدة: {booking.duration_days} يوم\n"
            value += f"⏳ {formatters.format_time_remaining(booking.scheduled_time)}"
            
            embed.add_field(
                name=f"{emoji} {type_name} - #{booking.booking_id}",
                value=value,
                inline=False
            )
        
        if self.total_pages > 1:
            embed.set_footer(text=f"صفحة {self.page + 1}/{self.total_pages} | المجموع: {len(self.bookings)}")
        else:
            embed.set_footer(text=f"المجموع: {len(self.bookings)}")
        
        return embed
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من المستخدم"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return False
        return True

class BookingsCog(commands.Cog):
    """نظام الحجوزات"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='حجز', description='📝 إنشاء حجز جديد - استخدم /start للواجهة التفاعلية')
    async def book(self, interaction: discord.Interaction):
        """إنشاء حجز جديد - توجيه للقائمة الرئيسية"""
        from cogs.main_menu import MainMenuView
        from utils.translator import get_text
        
        user_id = str(interaction.user.id)
        await translator.load_user_language_from_db(db, user_id)
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(user_id, is_admin)
        
        embed = create_colored_embed(
            "💡 استخدم الواجهة التفاعلية",
            "✨ الآن يمكنك استخدام الواجهة التفاعلية الجديدة!\n\n"
            "👇 اضغط على زر **📅 حجز موعد** من القائمة أدناه\n"
            "أو استخدم الأمر `/start` للوصول السريع",
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name='مواعيدي', description='📅 عرض حجوزاتك - استخدم /start للواجهة التفاعلية')
    async def my_bookings(self, interaction: discord.Interaction):
        """عرض حجوزات المستخدم"""
        await interaction.response.defer(ephemeral=True)
        
        user = await db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            # توجيه للقائمة الرئيسية
            from cogs.main_menu import MainMenuView
            user_id = str(interaction.user.id)
            await translator.load_user_language_from_db(db, user_id)
            is_admin = permissions.is_admin(interaction.user)
            view = MainMenuView(user_id, is_admin)
            
            embed = create_colored_embed(
                "💡 مرحباً بك!",
                "✨ استخدم الواجهة التفاعلية لإدارة حجوزاتك\n\n"
                "👇 اضغط على **📅 حجز موعد** لإنشاء حجز جديد",
                'info'
            )
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            return
        
        bookings = await db.get_user_bookings(user.user_id, 'active')
        
        if not bookings:
            await interaction.followup.send(
                embed=create_colored_embed("لا توجد حجوزات", "ليس لديك حجوزات نشطة حالياً.", 'info'),
                ephemeral=True
            )
            return
        
        # استخدام العرض الجديد مع الأزرار
        view = BookingsListView(bookings, str(interaction.user.id), f"📅 حجوزاتك النشطة ({len(bookings)})")
        embed = view.create_embed()
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name='إلغاء', description='❌ إلغاء حجز - استخدم /start ثم اضغط مواعيدي')
    @app_commands.describe(booking_id='رقم الحجز المراد إلغاؤه')
    async def cancel(self, interaction: discord.Interaction, booking_id: int):
        """إلغاء حجز - توجيه للقائمة التفاعلية"""
        from cogs.main_menu import MainMenuView
        from utils.translator import get_text
        
        user_id = str(interaction.user.id)
        await translator.load_user_language_from_db(db, user_id)
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(user_id, is_admin)
        
        embed = create_colored_embed(
            "💡 استخدم الواجهة التفاعلية",
            f"✨ الآن يمكنك إدارة حجوزاتك من الواجهة التفاعلية!\n\n"
            f"👇 اضغط على زر **📋 مواعيدي** من القائمة أدناه\n"
            f"ثم اضغط على **❌ إلغاء** بجانب الحجز #{booking_id}\n\n"
            f"أو استخدم الأمر `/start` للوصول السريع",
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name='جدول', description='📊 عرض جدول المواعيد - استخدم /start ثم اضغط جدول المواعيد')
    @app_commands.describe(نوع='نوع الحجز: building, research, training')
    @app_commands.choices(نوع=[
        app_commands.Choice(name='🏗️ البناء', value='building'),
        app_commands.Choice(name='🔬 الأبحاث', value='research'),
        app_commands.Choice(name='⚔️ التدريب', value='training'),
        app_commands.Choice(name='📅 الكل', value='all')
    ])
    async def schedule(self, interaction: discord.Interaction, نوع: str = 'all'):
        """عرض جدول المواعيد - توجيه للقائمة التفاعلية"""
        from cogs.main_menu import MainMenuView
        from utils.translator import get_text
        
        user_id = str(interaction.user.id)
        await translator.load_user_language_from_db(db, user_id)
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(user_id, is_admin)
        
        booking_name = "الكل"
        if نوع != 'all':
            booking_info = config.BOOKING_TYPES.get(نوع, {})
            booking_name = booking_info.get('name', نوع)
        
        embed = create_colored_embed(
            "💡 استخدم الواجهة التفاعلية",
            f"✨ الآن يمكنك عرض جدول المواعيد من الواجهة التفاعلية!\n\n"
            f"👇 اضغط على زر **📊 جدول المواعيد** من القائمة أدناه\n"
            f"لعرض مواعيد: {booking_name}\n\n"
            f"أو استخدم الأمر `/start` للوصول السريع",
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(BookingsCog(bot))
