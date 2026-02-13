"""
نظام الإحصائيات والنقاط - Stats Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging

from database import db
from utils import embeds
from config import config

logger = logging.getLogger('stats')

class StatsCog(commands.Cog):
    """نظام الإحصائيات والنقاط"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='mystats', description='📊 عرض إحصائياتك')
    async def my_stats(self, interaction: discord.Interaction):
        """عرض إحصائيات المستخدم"""
        await interaction.response.defer(ephemeral=True)
        
        user = await db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            await interaction.followup.send(
                embed=embeds.create_info_embed("لا توجد بيانات", "ليس لديك أي نشاط بعد."),
                ephemeral=True
            )
            return
        
        embed = embeds.create_stats_embed(user)
        
        # الإنجازات
        achievements = await db.get_user_achievements(user.user_id)
        if achievements:
            achievements_text = ""
            for achievement in achievements[:5]:
                achievements_text += f"• {achievement.achievement_name}\n"
            embed.add_field(name="🏆 الإنجازات", value=achievements_text, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name='leaderboard', description='🏆 لوحة المتصدرين')
    @app_commands.describe(عدد='عدد اللاعبين (1-50)')
    async def leaderboard(self, interaction: discord.Interaction, عدد: int = 10):
        """عرض لوحة المتصدرين"""
        await interaction.response.defer()
        
        عدد = max(1, min(عدد, 50))
        
        top_users = await db.get_leaderboard(عدد)
        
        if not top_users:
            await interaction.followup.send(
                embed=embeds.create_info_embed("لا توجد بيانات", "لا يوجد لاعبون بعد.")
            )
            return
        
        embed = embeds.create_leaderboard_embed(top_users)
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name='complete', description='✅ تأكيد إكمال حجز')
    @app_commands.describe(booking_id='رقم الحجز')
    async def complete_booking(self, interaction: discord.Interaction, booking_id: int):
        """تأكيد إكمال حجز"""
        await interaction.response.defer(ephemeral=True)
        
        booking = await db.get_booking(booking_id)
        if not booking:
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", f"لم يتم العثور على الحجز #{booking_id}"),
                ephemeral=True
            )
            return
        
        # التحقق من الصلاحيات
        from utils.permissions import permissions
        if not permissions.can_manage_booking(interaction.user, booking.created_by):
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "ليس لديك صلاحية لإدارة هذا الحجز"),
                ephemeral=True
            )
            return
        
        if booking.status != 'active':
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "هذا الحجز غير نشط"),
                ephemeral=True
            )
            return
        
        # تحديث الحجز
        await db.complete_booking(booking_id)
        
        # حساب النقاط
        points = config.POINTS_COMPLETED
        
        # نقاط إضافية للالتزام بالموعد
        from utils.datetime_helper import datetime_helper
        if not datetime_helper.is_past(booking.scheduled_time):
            points += config.POINTS_ON_TIME
        
        await db.update_user_points(booking.user_id, points)
        await db.update_user_stats(booking.user_id, 'completed')
        
        # التحقق من الإنجازات
        user = await db.get_user_by_discord_id(booking.created_by)
        if user:
            # إنجاز 100 حجز
            if user.completed_bookings + 1 >= 100:
                await db.award_achievement(
                    user.user_id,
                    'perfect_player',
                    config.ACHIEVEMENTS['perfect_player']['name']
                )
        
        await db.log_action(
            'booking_completed',
            f"تم إكمال الحجز #{booking_id}",
            str(interaction.user.id),
            booking_id,
            f"النقاط المكتسبة: {points}"
        )
        
        await interaction.followup.send(
            embed=embeds.create_success_embed(
                "تم الإنجاز! 🎉",
                f"تم تأكيد إكمال الحجز #{booking_id}\n⭐ حصلت على **{points}** نقطة!"
            ),
            ephemeral=True
        )
        
        logger.info(f"تم إكمال الحجز #{booking_id} بواسطة {interaction.user.name}")

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(StatsCog(bot))
