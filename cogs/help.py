"""
Help System - نظام المساعدة
Complete with /start, /menu, and /help commands
"""
import discord
from discord import app_commands
from discord.ext import commands
from config import config

class HelpCog(commands.Cog):
    """Help System"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='start', description='📖 Main Menu - القائمة الرئيسية')
    async def start(self, interaction: discord.Interaction):
        """Main menu"""
        embed = discord.Embed(
            title="📖 Main Menu - القائمة الرئيسية",
            description="**Welcome to Whiteout Survival Booking Bot!**\n\nمرحباً بك في بوت المواعيد!",
            color=0x3498db
        )
        
        embed.add_field(
            name="📅 Bookings - الحجوزات",
            value=(
                "`/حجز` - Create new booking | إنشاء حجز\n"
                "`/مواعيدي` - View bookings | عرض الحجوزات\n"
                "`/إلغاء [id]` - Cancel | إلغاء حجز\n"
                "`/جدول [type]` - Schedule | الجدول"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Statistics - الإحصائيات",
            value=(
                "`/mystats` - Your stats | إحصائياتك\n"
                "`/leaderboard` - Top players | المتصدرون\n"
                "`/complete [id]` - Complete | إكمال"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🤝 Alliances - التحالفات",
            value=(
                "`/alliance create` - Create | إنشاء\n"
                "`/alliance join` - Join | انضمام\n"
                "`/alliance info` - Info | معلومات"
            ),
            inline=False
        )
        
        embed.add_field(
            name="❓ Help - المساعدة",
            value="`/help` - Full guide | الدليل الكامل",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name='menu', description='📖 Main Menu - القائمة الرئيسية')
    async def menu(self, interaction: discord.Interaction):
        """Main menu - same as /start command | القائمة الرئيسية"""
        await self.start(interaction)
    
    @app_commands.command(name='help', description='❓ Full Help Guide - دليل المساعدة')
    async def help(self, interaction: discord.Interaction):
        """Complete help guide - shown privately (ephemeral) to avoid channel clutter"""
        embed = discord.Embed(
            title="📖 Complete Help Guide",
            description="Full guide for using the bot",
            color=0x3498db
        )
        
        embed.add_field(
            name="🚀 Quick Start",
            value=(
                "1. Type `/start` or `/menu`\n"
                "2. Choose a command\n"
                "3. Follow instructions!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📅 Booking Commands",
            value=(
                "`/حجز` - Create new booking\n"
                "`/مواعيدي` - View your bookings\n"
                "`/إلغاء [id]` - Cancel booking\n"
                "`/جدول [type]` - View schedule\n"
                "`/complete [id]` - Mark as complete"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Statistics",
            value=(
                "`/mystats` - Your personal stats\n"
                "`/leaderboard [count]` - Top players"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🤝 Alliances",
            value=(
                "`/alliance create [name]` - Create alliance\n"
                "`/alliance join [name]` - Join alliance\n"
                "`/alliance leave` - Leave alliance\n"
                "`/alliance info [name]` - Alliance info"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Admin (Admins Only)",
            value=(
                "`/admin stats` - Bot statistics\n"
                "`/admin export` - Export data\n"
                "`/admin backup` - Create backup"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⭐ Points System",
            value=(
                f"+{config.POINTS_COMPLETED} points per completed booking\n"
                f"+{config.POINTS_ON_TIME} bonus for on-time\n"
                f"{config.POINTS_CANCELLED} penalty for cancellation"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use /start for quick menu")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup cog"""
    await bot.add_cog(HelpCog(bot))
