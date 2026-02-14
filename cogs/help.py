"""
Help System - نظام المساعدة
Complete with /start, /menu, and /help commands with interactive buttons
"""
import discord
from discord import app_commands
from discord.ext import commands
from config import config
from utils.buttons import MainMenuView

class HelpCog(commands.Cog):
    """Help System"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='start', description='🎮 ابدأ استخدام البوت - Start using the bot')
    async def start(self, interaction: discord.Interaction):
        """أمر البداية مع القائمة الرئيسية التفاعلية"""
        embed = discord.Embed(
            title="🎮 مرحباً بك في بوت حجز المواعيد!",
            description=(
                "**بوت احترافي لإدارة مواعيد لعبة النجاة في الصقيع**\n\n"
                "🎯 **الميزات:**\n"
                "• 📝 حجز المواعيد (بناء، أبحاث، تدريب)\n"
                "• 🔔 تذكيرات تلقائية\n"
                "• 📊 نظام النقاط والإنجازات\n"
                "• 🏰 التحالفات والمنافسة\n\n"
                "**اختر من القائمة بالأسفل للبدء:**"
            ),
            color=discord.Color.blue()
        )
        
        if self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(
            name="💡 نصيحة",
            value="استخدم الأزرار التفاعلية بالأسفل للتنقل بسهولة!",
            inline=False
        )
        
        embed.set_footer(text=f"مرحباً {interaction.user.name} | استخدم /help للمزيد من المعلومات")
        
        view = MainMenuView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name='menu', description='📋 القائمة الرئيسية - Main Menu')
    async def menu(self, interaction: discord.Interaction):
        """عرض القائمة الرئيسية التفاعلية"""
        embed = discord.Embed(
            title="📋 القائمة الرئيسية",
            description="اختر ما تريد القيام به من الأزرار بالأسفل:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📝 الحجوزات",
            value="إنشاء حجز جديد أو عرض حجوزاتك الحالية",
            inline=False
        )
        
        embed.add_field(
            name="📊 الإحصائيات",
            value="اعرض نقاطك وإنجازاتك الشخصية",
            inline=False
        )
        
        embed.add_field(
            name="🏰 التحالفات",
            value="إدارة تحالفك أو الانضمام لتحالف جديد",
            inline=False
        )
        
        view = MainMenuView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
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
