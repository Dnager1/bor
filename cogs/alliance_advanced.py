"""
نظام التحالفات المتقدم - Advanced Alliance System  
Full-featured alliance system with member management, join requests, and more
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional, List
from datetime import datetime

from database import db
from database.models import Alliance, AllianceMember, AllianceJoinRequest
from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed, PaginationView, ConfirmView
from utils import validators, permissions

logger = logging.getLogger('alliance_advanced')

class AllianceCreateModal(discord.ui.Modal):
    """نموذج إنشاء تحالف"""
    
    def __init__(self, user_id: str):
        super().__init__(title='🏰 إنشاء تحالف جديد')
        self.user_id = user_id
    
    name = discord.ui.TextInput(
        label='اسم التحالف | Alliance Name',
        placeholder='مثال: Warriors of the North',
        required=True,
        min_length=2,
        max_length=30
    )
    
    logo = discord.ui.TextInput(
        label='شعار التحالف | Logo (emoji)',
        placeholder='مثال: 🏰 أو ⚔️ أو 🛡️',
        required=False,
        max_length=2,
        default='🏰'
    )
    
    description = discord.ui.TextInput(
        label='وصف التحالف | Description',
        placeholder='وصف قصير عن التحالف...',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    max_members = discord.ui.TextInput(
        label='الحد الأقصى للأعضاء | Max Members',
        placeholder='مثال: 50 (من 10 إلى 100)',
        required=False,
        default='50',
        max_length=3
    )
    
    requirements = discord.ui.TextInput(
        label='متطلبات الانضمام | Requirements',
        placeholder='مثال: مستوى 10+، نشط يومياً',
        required=False,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """عند إرسال النموذج"""
        await interaction.response.defer(ephemeral=True)
        
        # التحقق من الاسم
        valid, error = validators.validate_alliance_name(self.name.value)
        if not valid:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(self.user_id, 'common.error'),
                    error,
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # التحقق من عدم وجود تحالف بنفس الاسم
        existing = await db.get_alliance_by_name(self.name.value)
        if existing:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(self.user_id, 'common.error'),
                    get_text(self.user_id, 'alliance.name_exists'),
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # التحقق من الحد الأقصى للأعضاء
        try:
            max_members = int(self.max_members.value) if self.max_members.value else 50
            if max_members < 10 or max_members > 100:
                await interaction.followup.send(
                    embed=create_colored_embed(
                        get_text(self.user_id, 'common.error'),
                        "يجب أن يكون الحد الأقصى للأعضاء بين 10 و 100",
                        'error'
                    ),
                    ephemeral=True
                )
                return
        except ValueError:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(self.user_id, 'common.error'),
                    "يجب إدخال رقم صحيح للحد الأقصى للأعضاء",
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # الحصول على المستخدم
        user = await db.get_user_by_discord_id(self.user_id)
        if not user:
            user = await db.get_or_create_user(
                self.user_id,
                interaction.user.name,
                '00000'
            )
        
        # التحقق من عدم انتماء المستخدم لتحالف آخر
        if user.alliance_id:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(self.user_id, 'common.error'),
                    get_text(self.user_id, 'alliance.already_member'),
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # إنشاء التحالف
        try:
            logo = self.logo.value if self.logo.value else '🏰'
            
            alliance_id = await db.execute(
                """INSERT INTO alliances 
                   (name, description, leader_id, alliance_logo, max_members, 
                    requirements, alliance_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (self.name.value, self.description.value, user.user_id,
                 logo, max_members, self.requirements.value, 'public')
            )
            alliance_id = alliance_id.lastrowid
            
            # إضافة المستخدم كقائد للتحالف
            await db.execute(
                """INSERT INTO alliance_members 
                   (user_id, alliance_id, rank, contribution_points)
                   VALUES (?, ?, 'leader', 0)""",
                (user.user_id, alliance_id)
            )
            
            # تحديث معرف التحالف للمستخدم
            await db.execute(
                "UPDATE users SET alliance_id = ? WHERE user_id = ?",
                (alliance_id, user.user_id)
            )
            
            # تسجيل العملية
            await db.log_action(
                'alliance_created',
                f"تم إنشاء التحالف: {self.name.value}",
                self.user_id,
                details=f"شعار: {logo}, الحد الأقصى: {max_members}"
            )
            
            logger.info(f"تم إنشاء التحالف {self.name.value} بواسطة {interaction.user.name}")
            
            # إنشاء رسالة النجاح
            embed = create_colored_embed(
                get_text(self.user_id, 'alliance.created_success'),
                f"{logo} **{self.name.value}**\n\n"
                f"📝 {self.description.value}\n"
                f"👥 الحد الأقصى: {max_members} عضو\n"
                f"✅ تم إنشاء التحالف بنجاح وأنت الآن قائده!",
                'success'
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء التحالف: {e}")
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(self.user_id, 'common.error'),
                    "حدث خطأ أثناء إنشاء التحالف",
                    'error'
                ),
                ephemeral=True
            )

class AllianceMenuView(discord.ui.View):
    """قائمة التحالفات الرئيسية"""
    
    def __init__(self, user_id: str, cog):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.cog = cog
    
    @discord.ui.button(label="🏰 إنشاء تحالف", style=discord.ButtonStyle.primary, row=0)
    async def create_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إنشاء تحالف"""
        modal = AllianceCreateModal(self.user_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔍 البحث عن تحالف", style=discord.ButtonStyle.primary, row=0)
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر البحث عن تحالف"""
        await self.cog._show_alliance_list(interaction)
    
    @discord.ui.button(label="📜 تحالفي", style=discord.ButtonStyle.secondary, row=1)
    async def my_alliance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر تحالفي"""
        await self.cog._show_my_alliance(interaction)
    
    @discord.ui.button(label="👥 إدارة الأعضاء", style=discord.ButtonStyle.secondary, row=1)
    async def manage_members_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إدارة الأعضاء"""
        await interaction.response.send_message(
            "🏗️ نظام إدارة الأعضاء قيد التطوير...",
            ephemeral=True
        )
    
    @discord.ui.button(label="📊 إحصائيات التحالف", style=discord.ButtonStyle.secondary, row=1)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إحصائيات التحالف"""
        await self.cog._show_alliance_stats(interaction)
    
    @discord.ui.button(label="🏆 لوحة المتصدرين", style=discord.ButtonStyle.secondary, row=2)
    async def leaderboard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر لوحة المتصدرين"""
        await interaction.response.send_message(
            "🏗️ لوحة متصدرين التحالفات قيد التطوير...",
            ephemeral=True
        )
    
    @discord.ui.button(label="🚪 مغادرة التحالف", style=discord.ButtonStyle.danger, row=2)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر مغادرة التحالف"""
        await self.cog._leave_alliance(interaction)
    
    @discord.ui.button(label="🔙 رجوع للقائمة الرئيسية", style=discord.ButtonStyle.secondary, row=3)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر الرجوع"""
        from cogs.main_menu import MainMenuView
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(self.user_id, is_admin)
        
        embed = create_colored_embed(
            get_text(self.user_id, 'main_menu.title'),
            get_text(self.user_id, 'main_menu.description'),
            'info'
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من المستخدم"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ هذه القائمة ليست لك!",
                ephemeral=True
            )
            return False
        return True

class AllianceAdvancedCog(commands.Cog):
    """نظام التحالفات المتقدم"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='تحالفات', description='🤝 نظام التحالفات المتقدم')
    async def alliances_menu(self, interaction: discord.Interaction):
        """قائمة التحالفات الرئيسية"""
        user_id = str(interaction.user.id)
        
        # تحميل لغة المستخدم
        await translator.load_user_language_from_db(db, user_id)
        
        view = AllianceMenuView(user_id, self)
        
        embed = create_colored_embed(
            get_text(user_id, 'alliance.menu_title'),
            get_text(user_id, 'alliance.menu_desc'),
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _show_alliance_list(self, interaction: discord.Interaction):
        """عرض قائمة التحالفات المتاحة"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        # جلب جميع التحالفات
        alliances_data = await db.fetchall(
            """SELECT alliance_id, name, description, alliance_logo, 
                      member_count, max_members, alliance_type, requirements
               FROM alliances 
               ORDER BY member_count DESC, name ASC"""
        )
        
        if not alliances_data:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.info'),
                    "لا توجد تحالفات متاحة حالياً",
                    'info'
                ),
                ephemeral=True
            )
            return
        
        # إنشاء قائمة التحالفات
        embed = create_colored_embed(
            "🔍 قائمة التحالفات المتاحة",
            f"عدد التحالفات: {len(alliances_data)}",
            'info'
        )
        
        for alliance in alliances_data[:10]:  # عرض أول 10 تحالفات
            logo = alliance[3] or '🏰'
            name = alliance[1]
            desc = alliance[2] or "لا يوجد وصف"
            members = alliance[4]
            max_members = alliance[5]
            alliance_type = "🔒 خاص" if alliance[6] == 'private' else "🌐 عام"
            requirements = alliance[7] or "بدون متطلبات"
            
            embed.add_field(
                name=f"{logo} {name} {alliance_type}",
                value=f"📝 {desc[:50]}...\n"
                      f"👥 الأعضاء: {members}/{max_members}\n"
                      f"📋 المتطلبات: {requirements[:40]}",
                inline=False
            )
        
        if len(alliances_data) > 10:
            embed.set_footer(text=f"عرض 10 من {len(alliances_data)} تحالف")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _show_my_alliance(self, interaction: discord.Interaction):
        """عرض معلومات تحالف المستخدم"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        # الحصول على المستخدم
        user = await db.get_user_by_discord_id(user_id)
        if not user or not user.alliance_id:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    get_text(user_id, 'alliance.not_member'),
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # الحصول على معلومات التحالف
        alliance_data = await db.fetchone(
            """SELECT alliance_id, name, description, alliance_logo, leader_id,
                      member_count, max_members, total_bookings, total_points,
                      completed_bookings, alliance_rank, created_at
               FROM alliances WHERE alliance_id = ?""",
            (user.alliance_id,)
        )
        
        if not alliance_data:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    get_text(user_id, 'alliance.not_found'),
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # الحصول على رتبة المستخدم في التحالف
        member_data = await db.fetchone(
            "SELECT rank FROM alliance_members WHERE user_id = ? AND alliance_id = ?",
            (user.user_id, user.alliance_id)
        )
        rank = member_data[0] if member_data else 'member'
        
        # بناء الـ embed
        logo = alliance_data[3] or '🏰'
        name = alliance_data[1]
        desc = alliance_data[2] or "لا يوجد وصف"
        
        embed = discord.Embed(
            title=f"{logo} {name}",
            description=desc,
            color=0x9b59b6
        )
        
        # رتبة المستخدم
        rank_emoji = {
            'leader': '👑',
            'deputy': '⭐',
            'member': '👤'
        }
        rank_name = {
            'leader': 'قائد',
            'deputy': 'نائب',
            'member': 'عضو'
        }
        embed.add_field(
            name="رتبتك",
            value=f"{rank_emoji.get(rank, '👤')} {rank_name.get(rank, 'عضو')}",
            inline=True
        )
        
        # الإحصائيات
        embed.add_field(name="👥 الأعضاء", value=f"{alliance_data[5]}/{alliance_data[6]}", inline=True)
        embed.add_field(name="⭐ النقاط", value=str(alliance_data[8]), inline=True)
        embed.add_field(name="📅 الحجوزات النشطة", value=str(alliance_data[7]), inline=True)
        embed.add_field(name="✅ الحجوزات المكتملة", value=str(alliance_data[9]), inline=True)
        embed.add_field(name="🏆 الترتيب", value=f"#{alliance_data[10]}" if alliance_data[10] > 0 else "غير مصنف", inline=True)
        
        from utils.formatters import formatters
        if alliance_data[11]:
            embed.add_field(
                name="📆 تاريخ الإنشاء",
                value=formatters.format_datetime(datetime.fromisoformat(alliance_data[11]), include_time=False),
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _show_alliance_stats(self, interaction: discord.Interaction):
        """عرض إحصائيات التحالف"""
        await self._show_my_alliance(interaction)
    
    async def _leave_alliance(self, interaction: discord.Interaction):
        """مغادرة التحالف"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        # الحصول على المستخدم
        user = await db.get_user_by_discord_id(user_id)
        if not user or not user.alliance_id:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    get_text(user_id, 'alliance.not_member'),
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # الحصول على معلومات التحالف
        alliance = await db.get_alliance(user.alliance_id)
        if not alliance:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    get_text(user_id, 'alliance.not_found'),
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # التحقق من أن المستخدم ليس القائد
        if alliance.leader_id == user.user_id:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    "لا يمكن للقائد مغادرة التحالف. يجب نقل القيادة أو حذف التحالف.",
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # مغادرة التحالف
        try:
            await db.leave_alliance(user.user_id, user.alliance_id)
            
            await db.log_action(
                'alliance_left',
                f"غادر التحالف: {alliance.name}",
                user_id
            )
            
            logger.info(f"{interaction.user.name} غادر التحالف {alliance.name}")
            
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'alliance.left_success'),
                    f"غادرت تحالف **{alliance.name}** بنجاح",
                    'success'
                ),
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"خطأ في مغادرة التحالف: {e}")
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    "حدث خطأ أثناء مغادرة التحالف",
                    'error'
                ),
                ephemeral=True
            )

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(AllianceAdvancedCog(bot))
