"""
لوحة تحكم الأدمن المتقدمة - Advanced Admin Panel
Comprehensive admin control panel with button-based UI
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
import io
import csv
from datetime import datetime
import os

from database import db
from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed, ProgressBar
from utils import permissions, embeds
from config import config

logger = logging.getLogger('admin_panel')

class AdminPanelView(discord.ui.View):
    """لوحة تحكم الأدمن الرئيسية"""
    
    def __init__(self, user_id: str, cog):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.cog = cog
    
    @discord.ui.button(label="📊 إحصائيات البوت", style=discord.ButtonStyle.primary, row=0)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إحصائيات البوت"""
        await self.cog._show_bot_stats(interaction)
    
    @discord.ui.button(label="👥 إدارة المستخدمين", style=discord.ButtonStyle.primary, row=0)
    async def users_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إدارة المستخدمين"""
        await interaction.response.send_message(
            "🏗️ نظام إدارة المستخدمين قيد التطوير...",
            ephemeral=True
        )
    
    @discord.ui.button(label="🤝 إدارة التحالفات", style=discord.ButtonStyle.primary, row=0)
    async def alliances_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إدارة التحالفات"""
        await self.cog._manage_alliances(interaction)
    
    @discord.ui.button(label="📅 إدارة الحجوزات", style=discord.ButtonStyle.secondary, row=1)
    async def bookings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إدارة الحجوزات"""
        await interaction.response.send_message(
            "🏗️ نظام إدارة الحجوزات قيد التطوير...",
            ephemeral=True
        )
    
    @discord.ui.button(label="📢 إرسال إعلان", style=discord.ButtonStyle.secondary, row=1)
    async def announce_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر إرسال إعلان"""
        await interaction.response.send_message(
            "🏗️ نظام الإعلانات قيد التطوير...",
            ephemeral=True
        )
    
    @discord.ui.button(label="💾 نسخ احتياطي", style=discord.ButtonStyle.secondary, row=1)
    async def backup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر النسخ الاحتياطي"""
        await self.cog._create_backup(interaction)
    
    @discord.ui.button(label="📥 تصدير البيانات", style=discord.ButtonStyle.success, row=2)
    async def export_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر تصدير البيانات"""
        await self.cog._export_data(interaction)
    
    @discord.ui.button(label="📜 عرض السجلات", style=discord.ButtonStyle.success, row=2)
    async def logs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """زر عرض السجلات"""
        await self.cog._show_logs(interaction)
    
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
                "❌ هذه اللوحة ليست لك!",
                ephemeral=True
            )
            return False
        return True

class AdminPanelCog(commands.Cog):
    """نظام لوحة تحكم الأدمن المتقدمة"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='admin_panel', description='🛡️ لوحة تحكم الأدمن')
    async def admin_panel(self, interaction: discord.Interaction):
        """فتح لوحة تحكم الأدمن"""
        user_id = str(interaction.user.id)
        
        # التحقق من الصلاحيات
        if not permissions.is_admin(interaction.user):
            await interaction.response.send_message(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    get_text(user_id, 'admin.no_permission'),
                    'error'
                ),
                ephemeral=True
            )
            return
        
        # تحميل لغة المستخدم
        await translator.load_user_language_from_db(db, user_id)
        
        view = AdminPanelView(user_id, self)
        
        embed = create_colored_embed(
            get_text(user_id, 'admin.panel_title'),
            get_text(user_id, 'admin.panel_desc'),
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _show_bot_stats(self, interaction: discord.Interaction):
        """عرض إحصائيات البوت الشاملة"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        # جمع الإحصائيات
        stats = await db.get_stats()
        
        # حساب وقت التشغيل
        uptime = datetime.now() - self.bot.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{days} يوم، {hours} ساعة، {minutes} دقيقة"
        
        # حساب حجم قاعدة البيانات
        try:
            db_size = os.path.getsize(config.DATABASE_PATH) / (1024 * 1024)  # MB
            db_size_str = f"{db_size:.2f} MB"
        except:
            db_size_str = "غير متاح"
        
        # حساب معدل الإكمال
        total_completed_cancelled = stats['completed_bookings'] + stats['cancelled_bookings']
        completion_rate = (stats['completed_bookings'] / total_completed_cancelled * 100) if total_completed_cancelled > 0 else 0
        
        # بناء الـ embed
        embed = discord.Embed(
            title="📊 إحصائيات البوت الشاملة",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        # المستخدمون
        embed.add_field(
            name="👥 المستخدمون",
            value=f"**المجموع:** {stats['total_users']}\n"
                  f"**النشطون:** {stats.get('active_users', 'N/A')}",
            inline=True
        )
        
        # التحالفات
        embed.add_field(
            name="🤝 التحالفات",
            value=f"**عدد التحالفات:** {stats['total_alliances']}\n"
                  f"**إجمالي الأعضاء:** {stats.get('alliance_members', 'N/A')}",
            inline=True
        )
        
        # الحجوزات
        embed.add_field(
            name="📅 الحجوزات",
            value=f"**النشطة:** {stats['active_bookings']}\n"
                  f"**المكتملة:** {stats['completed_bookings']}\n"
                  f"**الملغاة:** {stats['cancelled_bookings']}",
            inline=True
        )
        
        # معدل الإكمال
        progress_bar = ProgressBar.create(stats['completed_bookings'], total_completed_cancelled, length=10)
        embed.add_field(
            name="📈 معدل الإكمال",
            value=f"{progress_bar}\n**{completion_rate:.1f}%**",
            inline=False
        )
        
        # معلومات النظام
        embed.add_field(
            name="⚙️ معلومات النظام",
            value=f"**وقت التشغيل:** {uptime_str}\n"
                  f"**عدد السيرفرات:** {len(self.bot.guilds)}\n"
                  f"**حجم قاعدة البيانات:** {db_size_str}",
            inline=False
        )
        
        # أفضل اللاعبين
        top_users = await db.get_leaderboard(5)
        if top_users:
            users_text = ""
            for i, user in enumerate(top_users, 1):
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
                users_text += f"{medal} **{user.username}** - {user.points} نقطة\n"
            embed.add_field(name="🏆 أفضل 5 لاعبين", value=users_text, inline=False)
        
        embed.set_footer(text=f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _manage_alliances(self, interaction: discord.Interaction):
        """إدارة التحالفات"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        # جلب جميع التحالفات
        alliances_data = await db.fetchall(
            """SELECT alliance_id, name, alliance_logo, leader_id, member_count, 
                      max_members, total_points, total_bookings, created_at
               FROM alliances 
               ORDER BY total_points DESC, name ASC"""
        )
        
        if not alliances_data:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.info'),
                    "لا توجد تحالفات في النظام",
                    'info'
                ),
                ephemeral=True
            )
            return
        
        # بناء الـ embed
        embed = discord.Embed(
            title="🤝 إدارة التحالفات",
            description=f"عدد التحالفات: {len(alliances_data)}",
            color=0x9b59b6
        )
        
        for alliance in alliances_data[:15]:  # عرض أول 15 تحالف
            logo = alliance[2] or '🏰'
            name = alliance[1]
            members = alliance[4]
            max_members = alliance[5]
            points = alliance[6]
            bookings = alliance[7]
            
            embed.add_field(
                name=f"{logo} {name} (ID: {alliance[0]})",
                value=f"👥 الأعضاء: {members}/{max_members}\n"
                      f"⭐ النقاط: {points}\n"
                      f"📅 الحجوزات: {bookings}",
                inline=True
            )
        
        if len(alliances_data) > 15:
            embed.set_footer(text=f"عرض 15 من {len(alliances_data)} تحالف")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _create_backup(self, interaction: discord.Interaction):
        """إنشاء نسخة احتياطية"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        try:
            import shutil
            
            # إنشاء مجلد النسخ الاحتياطية إن لم يكن موجوداً
            os.makedirs(config.BACKUP_DIR, exist_ok=True)
            
            # إنشاء اسم ملف النسخة الاحتياطية
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{config.BACKUP_DIR}/backup_{timestamp}.db"
            
            # نسخ قاعدة البيانات
            shutil.copy2(config.DATABASE_PATH, backup_file)
            
            # حساب حجم النسخة الاحتياطية
            backup_size = os.path.getsize(backup_file) / (1024 * 1024)  # MB
            
            embed = create_colored_embed(
                "💾 نسخة احتياطية",
                f"✅ تم إنشاء نسخة احتياطية بنجاح!\n\n"
                f"📁 **الملف:** `{os.path.basename(backup_file)}`\n"
                f"📊 **الحجم:** {backup_size:.2f} MB\n"
                f"🕒 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                'success'
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(f"تم إنشاء نسخة احتياطية بواسطة {interaction.user.name}")
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.error'),
                    f"حدث خطأ أثناء إنشاء النسخة الاحتياطية:\n{str(e)}",
                    'error'
                ),
                ephemeral=True
            )
    
    async def _export_data(self, interaction: discord.Interaction):
        """تصدير البيانات إلى CSV"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # جلب كل الحجوزات
            bookings = await db.get_all_active_bookings()
            
            # إنشاء ملف CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # العناوين
            writer.writerow([
                'رقم الحجز', 'اسم اللاعب', 'معرف اللاعب', 'التحالف',
                'نوع الحجز', 'التاريخ', 'الوقت', 'عدد الأيام', 'الحالة', 'التفاصيل'
            ])
            
            # البيانات
            from utils.formatters import formatters
            for booking in bookings:
                writer.writerow([
                    booking.booking_id,
                    booking.player_name,
                    booking.player_id,
                    booking.alliance_name,
                    booking.booking_type,
                    formatters.format_datetime(booking.scheduled_time, include_time=False) if booking.scheduled_time else '',
                    booking.scheduled_time.strftime('%H:%M') if booking.scheduled_time else '',
                    booking.duration_days,
                    booking.status,
                    booking.details or ''
                ])
            
            # تحويل إلى ملف
            output.seek(0)
            file = discord.File(
                fp=io.BytesIO(output.getvalue().encode('utf-8-sig')),
                filename=f'bookings_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
            embed = create_colored_embed(
                "📥 تصدير البيانات",
                f"✅ تم تصدير {len(bookings)} حجز بنجاح!",
                'success'
            )
            
            await interaction.followup.send(
                embed=embed,
                file=file,
                ephemeral=True
            )
            
            logger.info(f"تم تصدير البيانات بواسطة {interaction.user.name}")
            
        except Exception as e:
            logger.error(f"خطأ في تصدير البيانات: {e}")
            await interaction.followup.send(
                embed=create_colored_embed(
                    "خطأ",
                    f"حدث خطأ أثناء تصدير البيانات:\n{str(e)}",
                    'error'
                ),
                ephemeral=True
            )
    
    async def _show_logs(self, interaction: discord.Interaction):
        """عرض السجلات الأخيرة"""
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        
        # جلب آخر 20 سجل
        logs_data = await db.fetchall(
            """SELECT action_type, description, user_id, created_at
               FROM logs 
               ORDER BY created_at DESC 
               LIMIT 20"""
        )
        
        if not logs_data:
            await interaction.followup.send(
                embed=create_colored_embed(
                    get_text(user_id, 'common.info'),
                    "لا توجد سجلات متاحة",
                    'info'
                ),
                ephemeral=True
            )
            return
        
        # بناء الـ embed
        embed = discord.Embed(
            title="📜 السجلات الأخيرة",
            description=f"آخر {len(logs_data)} عملية",
            color=0x95a5a6
        )
        
        for log in logs_data[:15]:
            action_type = log[0]
            description = log[1]
            user_id_log = log[2]
            created_at = log[3]
            
            # أيقونات حسب نوع العملية
            emoji_map = {
                'booking_created': '📅',
                'booking_completed': '✅',
                'booking_cancelled': '❌',
                'alliance_created': '🏰',
                'alliance_joined': '🤝',
                'alliance_left': '🚪',
                'user_updated': '👤'
            }
            emoji = emoji_map.get(action_type, '📝')
            
            from utils.formatters import formatters
            try:
                time_str = formatters.format_datetime(datetime.fromisoformat(created_at))
            except:
                time_str = created_at
            
            embed.add_field(
                name=f"{emoji} {action_type}",
                value=f"{description}\n🕒 {time_str}",
                inline=False
            )
        
        if len(logs_data) > 15:
            embed.set_footer(text=f"عرض 15 من {len(logs_data)} سجل")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(AdminPanelCog(bot))
