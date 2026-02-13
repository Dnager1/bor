"""
نظام الإحصائيات والنقاط - Stats Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging

from database import db
from utils import embeds
from utils.ui_components import create_colored_embed
from utils.translator import translator
from utils import permissions
from config import config

logger = logging.getLogger('stats')

class StatsCog(commands.Cog):
    """نظام الإحصائيات والنقاط"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='mystats', description='📊 عرض إحصائياتك - استخدم /start ثم اضغط إحصائياتي')
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
    
    @app_commands.command(name='leaderboard', description='🏆 لوحة المتصدرين - استخدم /start ثم اضغط المتصدرون')
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
    
    @app_commands.command(name='complete', description='✅ تأكيد إكمال حجز - استخدم /start ثم مواعيدي ثم إكمال')
    @app_commands.describe(booking_id='رقم الحجز')
    async def complete_booking(self, interaction: discord.Interaction, booking_id: int):
        """تأكيد إكمال حجز - توجيه للواجهة التفاعلية"""
        from cogs.main_menu import MainMenuView
        from utils.translator import get_text
        
        user_id = str(interaction.user.id)
        await translator.load_user_language_from_db(db, user_id)
        
        is_admin = permissions.is_admin(interaction.user)
        view = MainMenuView(user_id, is_admin)
        
        embed = create_colored_embed(
            "💡 استخدم الواجهة التفاعلية",
            f"✨ الآن يمكنك إكمال حجوزاتك من الواجهة التفاعلية!\n\n"
            f"👇 اضغط على زر **📋 مواعيدي** من القائمة أدناه\n"
            f"ثم اضغط على **✅ إكمال** بجانب الحجز #{booking_id}\n\n"
            f"أو استخدم الأمر `/start` للوصول السريع",
            'info'
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(StatsCog(bot))
