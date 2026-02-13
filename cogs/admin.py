"""
نظام الإدارة - Admin Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
import io
import csv
from datetime import datetime
import shutil
import os

from database import db
from utils import embeds, permissions
from config import config

logger = logging.getLogger('admin')

class AdminCog(commands.Cog):
    """نظام الإدارة"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """التحقق من صلاحيات الإدارة"""
        if not permissions.is_admin(interaction.user):
            await interaction.response.send_message(
                embed=embeds.create_error_embed("خطأ", "هذا الأمر متاح للمشرفين فقط!"),
                ephemeral=True
            )
            return False
        return True
    
    admin = app_commands.Group(name="admin", description="أوامر الإدارة")
    
    @admin.command(name='stats', description='📊 إحصائيات البوت')
    async def stats(self, interaction: discord.Interaction):
        """عرض إحصائيات شاملة"""
        await interaction.response.defer()
        
        stats = await db.get_stats()
        embed = embeds.create_admin_stats_embed(stats)
        
        # أفضل اللاعبين
        top_users = await db.get_leaderboard(5)
        if top_users:
            users_text = ""
            for i, user in enumerate(top_users, 1):
                users_text += f"{i}. **{user.username}** - {user.points} نقطة\n"
            embed.add_field(name="🏆 أفضل اللاعبين", value=users_text, inline=False)
        
        await interaction.followup.send(embed=embed)
        logger.info(f"تم عرض الإحصائيات بواسطة {interaction.user.name}")
    
    @admin.command(name='export', description='📥 تصدير البيانات إلى CSV')
    async def export(self, interaction: discord.Interaction):
        """تصدير البيانات"""
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
                'نوع الحجز', 'التاريخ', 'الوقت', 'الحالة', 'التفاصيل'
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
                    formatters.format_datetime(booking.scheduled_time, include_time=False),
                    booking.scheduled_time.strftime('%H:%M') if booking.scheduled_time else '',
                    booking.status,
                    booking.details or ''
                ])
            
            # تحويل إلى ملف
            output.seek(0)
            file = discord.File(
                fp=io.BytesIO(output.getvalue().encode('utf-8-sig')),
                filename=f'bookings_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
            await interaction.followup.send(
                embed=embeds.create_success_embed(
                    "تصدير البيانات",
                    f"تم تصدير {len(bookings)} حجز بنجاح"
                ),
                file=file,
                ephemeral=True
            )
            
            logger.info(f"تم تصدير البيانات بواسطة {interaction.user.name}")
            
        except Exception as e:
            logger.error(f"خطأ في تصدير البيانات: {e}")
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", f"فشل تصدير البيانات: {str(e)}"),
                ephemeral=True
            )
    
    @admin.command(name='backup', description='💾 نسخ احتياطي للقاعدة')
    async def backup(self, interaction: discord.Interaction):
        """إنشاء نسخة احتياطية"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # إنشاء مجلد النسخ الاحتياطي
            os.makedirs(config.BACKUP_DIR, exist_ok=True)
            
            # اسم ملف النسخة الاحتياطية
            backup_name = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            backup_path = os.path.join(config.BACKUP_DIR, backup_name)
            
            # نسخ قاعدة البيانات
            shutil.copy2(config.DATABASE_PATH, backup_path)
            
            # إرسال الملف
            file = discord.File(backup_path, filename=backup_name)
            
            await interaction.followup.send(
                embed=embeds.create_success_embed(
                    "نسخة احتياطية",
                    f"تم إنشاء نسخة احتياطية بنجاح\n📁 {backup_name}"
                ),
                file=file,
                ephemeral=True
            )
            
            logger.info(f"تم إنشاء نسخة احتياطية بواسطة {interaction.user.name}")
            
        except Exception as e:
            logger.error(f"خطأ في النسخ الاحتياطي: {e}")
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", f"فشل إنشاء نسخة احتياطية: {str(e)}"),
                ephemeral=True
            )
    
    @admin.command(name='announce', description='📢 إرسال إعلان')
    @app_commands.describe(رسالة='الرسالة المراد إرسالها')
    async def announce(self, interaction: discord.Interaction, رسالة: str):
        """إرسال إعلان لجميع الأعضاء النشطين"""
        await interaction.response.defer(ephemeral=True)
        
        # الحصول على كل المستخدمين ذوي الحجوزات النشطة
        bookings = await db.get_all_active_bookings()
        user_ids = set(booking.created_by for booking in bookings)
        
        sent_count = 0
        failed_count = 0
        
        embed = embeds.create_info_embed("📢 إعلان من الإدارة", رسالة)
        
        for user_id in user_ids:
            try:
                user = await self.bot.fetch_user(int(user_id))
                await user.send(embed=embed)
                sent_count += 1
            except:
                failed_count += 1
        
        await interaction.followup.send(
            embed=embeds.create_success_embed(
                "تم الإرسال",
                f"✅ تم إرسال الإعلان إلى {sent_count} مستخدم\n"
                f"❌ فشل الإرسال لـ {failed_count} مستخدم"
            ),
            ephemeral=True
        )
        
        logger.info(f"تم إرسال إعلان بواسطة {interaction.user.name} إلى {sent_count} مستخدم")
    
    @admin.command(name='clear', description='🗑️ حذف الحجوزات المنتهية')
    async def clear(self, interaction: discord.Interaction):
        """حذف الحجوزات المنتهية"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # تحديث الحجوزات المنتهية
            from utils.datetime_helper import datetime_helper
            now = datetime_helper.get_now()
            
            # الحصول على الحجوزات النشطة المنتهية
            bookings = await db.get_all_active_bookings()
            expired_count = 0
            
            for booking in bookings:
                if datetime_helper.is_past(booking.scheduled_time):
                    await db.update_booking_status(booking.booking_id, 'expired')
                    expired_count += 1
            
            await interaction.followup.send(
                embed=embeds.create_success_embed(
                    "تم التنظيف",
                    f"تم تحديث حالة {expired_count} حجز منتهي"
                ),
                ephemeral=True
            )
            
            logger.info(f"تم تنظيف {expired_count} حجز منتهي بواسطة {interaction.user.name}")
            
        except Exception as e:
            logger.error(f"خطأ في التنظيف: {e}")
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", f"فشل التنظيف: {str(e)}"),
                ephemeral=True
            )
    
    @admin.command(name='logs', description='📝 عرض السجلات')
    @app_commands.describe(عدد='عدد السجلات (1-100)')
    async def logs(self, interaction: discord.Interaction, عدد: int = 20):
        """عرض السجلات"""
        await interaction.response.defer(ephemeral=True)
        
        عدد = max(1, min(عدد, 100))
        
        logs = await db.get_logs(عدد)
        
        if not logs:
            await interaction.followup.send(
                embed=embeds.create_info_embed("السجلات", "لا توجد سجلات"),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📝 السجلات الأخيرة",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        from utils.formatters import formatters
        for log in logs[:10]:  # عرض أول 10 فقط في الرسالة
            value = f"**النوع:** {log.action_type}\n"
            value += f"**الوصف:** {log.description}\n"
            if log.created_at:
                value += f"**الوقت:** {formatters.format_datetime(log.created_at)}\n"
            
            embed.add_field(
                name=f"🔹 سجل #{log.log_id}",
                value=value,
                inline=False
            )
        
        embed.set_footer(text=f"عرض {min(len(logs), 10)} من {len(logs)} سجل")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(AdminCog(bot))
