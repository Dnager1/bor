"""
القائمة الرئيسية - Main Menu Cog
Professional button-based main menu system
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging

from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed
from utils import permissions

logger = logging.getLogger('main_menu')

class MainMenuView(discord.ui.View):
    """عرض القائمة الرئيسية بالأزرار"""
    
    def __init__(self, user_id: str, is_admin: bool = False):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.is_admin = is_admin
        self._build_menu()
    
    def _build_menu(self):
        """بناء أزرار القائمة"""
        user_id = self.user_id
        
        # الصف الأول - الحجوزات
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.book'),
            style=discord.ButtonStyle.primary,
            custom_id='btn_book',
            row=0
        ))
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.my_bookings'),
            style=discord.ButtonStyle.primary,
            custom_id='btn_my_bookings',
            row=0
        ))
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.schedule'),
            style=discord.ButtonStyle.primary,
            custom_id='btn_schedule',
            row=0
        ))
        
        # الصف الثاني - الإحصائيات والمتصدرون
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.stats'),
            style=discord.ButtonStyle.secondary,
            custom_id='btn_stats',
            row=1
        ))
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.leaderboard'),
            style=discord.ButtonStyle.secondary,
            custom_id='btn_leaderboard',
            row=1
        ))
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.alliance'),
            style=discord.ButtonStyle.secondary,
            custom_id='btn_alliance',
            row=1
        ))
        
        # الصف الثالث - الإدارة واللغة والمساعدة
        if self.is_admin:
            self.add_item(discord.ui.Button(
                label=get_text(user_id, 'main_menu.buttons.admin'),
                style=discord.ButtonStyle.danger,
                custom_id='btn_admin',
                row=2
            ))
        
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.language'),
            style=discord.ButtonStyle.secondary,
            custom_id='btn_language',
            row=2
        ))
        self.add_item(discord.ui.Button(
            label=get_text(user_id, 'main_menu.buttons.help'),
            style=discord.ButtonStyle.secondary,
            custom_id='btn_help',
            row=2
        ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من المستخدم"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return False
        return True

class LanguageSelectView(discord.ui.View):
    """عرض اختيار اللغة"""
    
    def __init__(self, user_id: str, cog):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.cog = cog
    
    @discord.ui.button(label="🇸🇦 العربية", style=discord.ButtonStyle.success, custom_id='lang_ar')
    async def arabic_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر اللغة العربية"""
        await self._change_language(interaction, 'ar')
    
    @discord.ui.button(label="🇬🇧 English", style=discord.ButtonStyle.success, custom_id='lang_en')
    async def english_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر اللغة الإنجليزية"""
        await self._change_language(interaction, 'en')
    
    @discord.ui.button(label="🔙 رجوع | Back", style=discord.ButtonStyle.secondary, custom_id='lang_back', row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر الرجوع"""
        from database import db
        await translator.load_user_language_from_db(db, self.user_id)
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(self.user_id, is_admin)
        
        embed = create_colored_embed(
            get_text(self.user_id, 'main_menu.title'),
            get_text(self.user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _change_language(self, interaction: discord.Interaction, lang_code: str):
        """تغيير اللغة"""
        from database import db
        
        # تعيين اللغة في المترجم
        translator.set_user_language(self.user_id, lang_code)
        
        # حفظ في قاعدة البيانات
        try:
            user = await db.get_user_by_discord_id(self.user_id)
            if user:
                await db.execute(
                    "UPDATE users SET language = ? WHERE user_id = ?",
                    (lang_code, user.user_id)
                )
        except Exception as e:
            logger.error(f"خطأ في حفظ اللغة: {e}")
        
        # إرسال رسالة نجاح
        embed = create_colored_embed(
            get_text(self.user_id, 'common.success'),
            get_text(self.user_id, 'language.changed'),
            'success'
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # إعادة فتح القائمة الرئيسية بعد ثانية
        import asyncio
        await asyncio.sleep(1)
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(self.user_id, is_admin)
        
        embed = create_colored_embed(
            get_text(self.user_id, 'main_menu.title'),
            get_text(self.user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.edit_original_response(embed=embed, view=view)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من المستخدم"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return False
        return True

class MainMenuCog(commands.Cog):
    """نظام القائمة الرئيسية"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='start', description='📖 فتح القائمة الرئيسية')
    async def start(self, interaction: discord.Interaction):
        """عرض القائمة الرئيسية"""
        await self._show_main_menu(interaction)
    
    @app_commands.command(name='menu', description='📖 فتح القائمة الرئيسية')
    async def menu(self, interaction: discord.Interaction):
        """عرض القائمة الرئيسية"""
        await self._show_main_menu(interaction)
    
    async def _show_main_menu(self, interaction: discord.Interaction):
        """عرض القائمة الرئيسية"""
        user_id = str(interaction.user.id)
        
        # تحميل لغة المستخدم من قاعدة البيانات
        from database import db
        await translator.load_user_language_from_db(db, user_id)
        
        # التحقق من صلاحيات الأدمن
        is_admin = permissions.is_admin(interaction.user)
        
        # إنشاء العرض
        view = MainMenuView(user_id, is_admin)
        
        # إنشاء الـ Embed
        embed = create_colored_embed(
            get_text(user_id, 'main_menu.title'),
            get_text(user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """معالجة تفاعلات الأزرار"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get('custom_id', '')
        user_id = str(interaction.user.id)
        
        # تحميل لغة المستخدم
        from database import db
        await translator.load_user_language_from_db(db, user_id)
        
        # معالجة كل زر
        if custom_id == 'btn_book':
            # فتح نظام الحجز
            await self._handle_book(interaction)
        
        elif custom_id == 'btn_my_bookings':
            # عرض حجوزات المستخدم
            await self._handle_my_bookings(interaction)
        
        elif custom_id == 'btn_schedule':
            # عرض جدول المواعيد
            await self._handle_schedule(interaction)
        
        elif custom_id == 'btn_stats':
            # عرض إحصائيات المستخدم
            await self._handle_stats(interaction)
        
        elif custom_id == 'btn_leaderboard':
            # عرض لوحة المتصدرين
            await self._handle_leaderboard(interaction)
        
        elif custom_id == 'btn_alliance':
            # فتح قائمة التحالفات
            await self._handle_alliance(interaction)
        
        elif custom_id == 'btn_admin':
            # فتح لوحة الأدمن
            await self._handle_admin(interaction)
        
        elif custom_id == 'btn_language':
            # فتح اختيار اللغة
            await self._handle_language(interaction)
        
        elif custom_id == 'btn_help':
            # عرض المساعدة
            await self._handle_help(interaction)
    
    async def _handle_book(self, interaction: discord.Interaction):
        """معالجة زر الحجز"""
        from cogs.bookings import BookingTypeView
        
        user_id = str(interaction.user.id)
        view = BookingTypeView(self.bot.get_cog('BookingsCog'))
        
        embed = create_colored_embed(
            get_text(user_id, 'booking.type_select_title'),
            get_text(user_id, 'booking.type_select_desc'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _handle_my_bookings(self, interaction: discord.Interaction):
        """معالجة زر مواعيدي"""
        # سيتم تنفيذه من خلال الـ cog الخاص بالحجوزات
        cog = self.bot.get_cog('BookingsCog')
        if cog:
            await cog.my_bookings(interaction)
        else:
            await interaction.response.send_message("❌ خطأ في النظام", ephemeral=True)
    
    async def _handle_schedule(self, interaction: discord.Interaction):
        """معالجة زر جدول المواعيد"""
        cog = self.bot.get_cog('BookingsCog')
        if cog:
            await cog.schedule(interaction)
        else:
            await interaction.response.send_message("❌ خطأ في النظام", ephemeral=True)
    
    async def _handle_stats(self, interaction: discord.Interaction):
        """معالجة زر الإحصائيات"""
        cog = self.bot.get_cog('StatsCog')
        if cog:
            await cog.my_stats(interaction)
        else:
            await interaction.response.send_message("❌ خطأ في النظام", ephemeral=True)
    
    async def _handle_leaderboard(self, interaction: discord.Interaction):
        """معالجة زر المتصدرين"""
        cog = self.bot.get_cog('StatsCog')
        if cog:
            await cog.leaderboard(interaction)
        else:
            await interaction.response.send_message("❌ خطأ في النظام", ephemeral=True)
    
    async def _handle_alliance(self, interaction: discord.Interaction):
        """معالجة زر التحالفات"""
        await interaction.response.send_message(
            "🏗️ نظام التحالفات المتقدم قيد التطوير...",
            ephemeral=True
        )
    
    async def _handle_admin(self, interaction: discord.Interaction):
        """معالجة زر الأدمن"""
        if not permissions.is_admin(interaction.user):
            await interaction.response.send_message(
                get_text(str(interaction.user.id), 'admin.no_permission'),
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            "🏗️ لوحة تحكم الأدمن المتقدمة قيد التطوير...",
            ephemeral=True
        )
    
    async def _handle_language(self, interaction: discord.Interaction):
        """معالجة زر اللغة"""
        user_id = str(interaction.user.id)
        view = LanguageSelectView(user_id, self)
        
        embed = create_colored_embed(
            get_text(user_id, 'language.select_title'),
            "",
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def _handle_help(self, interaction: discord.Interaction):
        """معالجة زر المساعدة"""
        cog = self.bot.get_cog('HelpCog')
        if cog:
            await cog.help_command(interaction)
        else:
            await interaction.response.send_message("❌ خطأ في النظام", ephemeral=True)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(MainMenuCog(bot))
