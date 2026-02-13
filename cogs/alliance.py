"""
نظام التحالفات - Alliance Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging

from database import db
from utils import embeds, validators
from config import config

logger = logging.getLogger('alliance')

class AllianceCog(commands.Cog):
    """نظام التحالفات"""
    
    def __init__(self, bot):
        self.bot = bot
    
    alliance = app_commands.Group(name="alliance", description="إدارة التحالفات")
    
    @alliance.command(name='create', description='🏰 إنشاء تحالف جديد')
    @app_commands.describe(
        اسم='اسم التحالف',
        وصف='وصف التحالف (اختياري)'
    )
    async def create(self, interaction: discord.Interaction, اسم: str, وصف: str = ''):
        """إنشاء تحالف جديد"""
        await interaction.response.defer(ephemeral=True)
        
        # التحقق من الاسم
        valid, error = validators.validate_alliance_name(اسم)
        if not valid:
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", error),
                ephemeral=True
            )
            return
        
        # التحقق من عدم وجود تحالف بنفس الاسم
        existing = await db.get_alliance_by_name(اسم)
        if existing:
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "يوجد تحالف بهذا الاسم بالفعل"),
                ephemeral=True
            )
            return
        
        # الحصول على المستخدم
        user = await db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            # إنشاء مستخدم مؤقت
            user = await db.get_or_create_user(
                str(interaction.user.id),
                interaction.user.name,
                '00000'
            )
        
        # التحقق من عدم انتماء المستخدم لتحالف آخر
        if user.alliance_id:
            await interaction.followup.send(
                embed=embeds.create_error_embed(
                    "خطأ",
                    "أنت عضو في تحالف آخر. يجب مغادرته أولاً."
                ),
                ephemeral=True
            )
            return
        
        # إنشاء التحالف
        alliance_id = await db.create_alliance(اسم, user.user_id, وصف)
        
        # إضافة المستخدم للتحالف
        await db.join_alliance(user.user_id, alliance_id)
        
        await db.log_action(
            'alliance_created',
            f"تم إنشاء التحالف: {اسم}",
            str(interaction.user.id),
            details=وصف
        )
        
        await interaction.followup.send(
            embed=embeds.create_success_embed(
                "تم إنشاء التحالف!",
                f"🏰 **{اسم}**\n\nتم إنشاء التحالف بنجاح وأنت الآن قائده!"
            ),
            ephemeral=True
        )
        
        logger.info(f"تم إنشاء التحالف {اسم} بواسطة {interaction.user.name}")
    
    @alliance.command(name='join', description='🤝 الانضمام لتحالف')
    @app_commands.describe(اسم='اسم التحالف')
    async def join(self, interaction: discord.Interaction, اسم: str):
        """الانضمام لتحالف"""
        await interaction.response.defer(ephemeral=True)
        
        # البحث عن التحالف
        alliance = await db.get_alliance_by_name(اسم)
        if not alliance:
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "لم يتم العثور على تحالف بهذا الاسم"),
                ephemeral=True
            )
            return
        
        # الحصول على المستخدم
        user = await db.get_user_by_discord_id(str(interaction.user.id))
        if not user:
            user = await db.get_or_create_user(
                str(interaction.user.id),
                interaction.user.name,
                '00000'
            )
        
        # التحقق من عدم الانتماء لتحالف
        if user.alliance_id:
            await interaction.followup.send(
                embed=embeds.create_error_embed(
                    "خطأ",
                    "أنت عضو في تحالف آخر. يجب مغادرته أولاً."
                ),
                ephemeral=True
            )
            return
        
        # الانضمام للتحالف
        await db.join_alliance(user.user_id, alliance.alliance_id)
        
        await db.log_action(
            'alliance_joined',
            f"انضم إلى التحالف: {اسم}",
            str(interaction.user.id)
        )
        
        await interaction.followup.send(
            embed=embeds.create_success_embed(
                "تم الانضمام!",
                f"🏰 انضممت إلى تحالف **{اسم}** بنجاح!"
            ),
            ephemeral=True
        )
        
        logger.info(f"{interaction.user.name} انضم إلى التحالف {اسم}")
    
    @alliance.command(name='leave', description='👋 مغادرة التحالف')
    async def leave(self, interaction: discord.Interaction):
        """مغادرة التحالف"""
        await interaction.response.defer(ephemeral=True)
        
        user = await db.get_user_by_discord_id(str(interaction.user.id))
        if not user or not user.alliance_id:
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "أنت لست عضواً في أي تحالف"),
                ephemeral=True
            )
            return
        
        alliance = await db.get_alliance(user.alliance_id)
        alliance_name = alliance.name if alliance else "غير معروف"
        
        # مغادرة التحالف
        await db.leave_alliance(user.user_id, user.alliance_id)
        
        await db.log_action(
            'alliance_left',
            f"غادر التحالف: {alliance_name}",
            str(interaction.user.id)
        )
        
        await interaction.followup.send(
            embed=embeds.create_success_embed(
                "تمت المغادرة",
                f"غادرت تحالف **{alliance_name}** بنجاح"
            ),
            ephemeral=True
        )
        
        logger.info(f"{interaction.user.name} غادر التحالف {alliance_name}")
    
    @alliance.command(name='info', description='ℹ️ معلومات التحالف')
    @app_commands.describe(اسم='اسم التحالف (اختياري)')
    async def info(self, interaction: discord.Interaction, اسم: str = None):
        """معلومات عن التحالف"""
        await interaction.response.defer()
        
        if اسم:
            alliance = await db.get_alliance_by_name(اسم)
        else:
            # عرض تحالف المستخدم
            user = await db.get_user_by_discord_id(str(interaction.user.id))
            if not user or not user.alliance_id:
                await interaction.followup.send(
                    embed=embeds.create_error_embed(
                        "خطأ",
                        "أنت لست عضواً في أي تحالف. حدد اسم تحالف أو انضم لواحد."
                    )
                )
                return
            alliance = await db.get_alliance(user.alliance_id)
        
        if not alliance:
            await interaction.followup.send(
                embed=embeds.create_error_embed("خطأ", "لم يتم العثور على التحالف")
            )
            return
        
        from utils.formatters import formatters
        embed = discord.Embed(
            title=f"🏰 {alliance.name}",
            description=alliance.description or "لا يوجد وصف",
            color=0x9b59b6
        )
        
        embed.add_field(name="👥 الأعضاء", value=str(alliance.member_count), inline=True)
        embed.add_field(name="📅 الحجوزات", value=str(alliance.total_bookings), inline=True)
        embed.add_field(name="⭐ النقاط", value=str(alliance.total_points), inline=True)
        
        if alliance.created_at:
            embed.add_field(
                name="📆 تاريخ الإنشاء",
                value=formatters.format_datetime(alliance.created_at, include_time=False),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(AllianceCog(bot))
