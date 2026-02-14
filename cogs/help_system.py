"""
نظام المساعدة - Help System
Complete help and documentation system
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging

from utils.translator import translator, get_text
from utils.ui_components import create_colored_embed

logger = logging.getLogger('help_system')


class HelpSystemCog(commands.Cog):
    """نظام المساعدة الكامل"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='help', description='📖 دليل المساعدة الشامل - Complete Help Guide')
    async def help(self, interaction: discord.Interaction):
        """عرض دليل المساعدة الشامل"""
        user_id = str(interaction.user.id)
        
        # Load user language
        from database import db
        await translator.load_user_language_from_db(db, user_id)
        
        embed = discord.Embed(
            title="📖 " + get_text(user_id, 'main_menu.title'),
            description="مرحباً بك في بوت إدارة النجاة في الصقيع\n\nWelcome to White Survival Management Bot",
            color=discord.Color.gold()
        )
        
        # Main Commands Section
        embed.add_field(
            name="🎮 الأوامر الرئيسية | Main Commands",
            value=(
                "`/start` - فتح القائمة الرئيسية | Open main menu\n"
                "`/help` - دليل المساعدة | Help guide\n"
            ),
            inline=False
        )
        
        # Alliance System
        embed.add_field(
            name="🤝 نظام التحالف | Alliance System",
            value=(
                "• عرض معلومات التحالف | View alliance info\n"
                "• إدارة الأعضاء | Manage members\n"
                "• نظام الرتب (R1-R5) | Rank system\n"
            ),
            inline=False
        )
        
        # Reservations System
        embed.add_field(
            name="📅 نظام الحجوزات | Reservations System",
            value=(
                "• **البناء** 🏗️ - حجز مواعيد البناء\n"
                "• **التدريب** ⚔️ - حجز مواعيد التدريب\n"
                "• **الأبحاث** 🔬 - حجز مواعيد الأبحاث\n"
                "• عرض حجوزاتي | View my reservations\n"
            ),
            inline=False
        )
        
        # Management System
        embed.add_field(
            name="⚙️ نظام الإدارة | Management System",
            value=(
                "• إحصائيات البوت | Bot statistics\n"
                "• إدارة المستخدمين | User management\n"
                "• إدارة التحالفات | Alliance management\n"
                "• نظام الصلاحيات | Permissions system\n"
                "*(متاح للإدارة فقط | Admins only)*\n"
            ),
            inline=False
        )
        
        # Reminders
        embed.add_field(
            name="⏰ نظام التذكيرات | Reminder System",
            value=(
                "يتم إرسال تذكيرات تلقائية:\n"
                "• قبل 24 ساعة | 24h before\n"
                "• قبل 6 ساعات | 6h before\n"
                "• قبل 3 ساعات | 3h before\n"
                "• قبل 1 ساعة | 1h before\n"
            ),
            inline=False
        )
        
        # Language System
        embed.add_field(
            name="🌐 نظام اللغة | Language System",
            value=(
                "• العربية 🇸🇦 | Arabic\n"
                "• English 🇬🇧 | English\n"
                "يتم حفظ اللغة المختارة تلقائياً\n"
                "Selected language is saved automatically"
            ),
            inline=False
        )
        
        # Navigation
        embed.add_field(
            name="🧭 التنقل | Navigation",
            value=(
                "استخدم الأزرار للتنقل بين القوائم\n"
                "Use buttons to navigate between menus\n"
                "زر الرجوع يعيدك للقائمة السابقة\n"
                "Back button returns to previous menu"
            ),
            inline=False
        )
        
        # Tips
        embed.add_field(
            name="💡 نصائح | Tips",
            value=(
                "• استخدم `/start` لفتح القائمة الرئيسية في أي وقت\n"
                "• Use `/start` to open main menu anytime\n"
                "• يمكنك إلغاء الحجز قبل موعده\n"
                "• You can cancel reservation before its time\n"
            ),
            inline=False
        )
        
        embed.set_footer(text="🎮 White Survival Management Bot | النجاة في الصقيع")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name='about', description='ℹ️ معلومات عن البوت - About the bot')
    async def about(self, interaction: discord.Interaction):
        """معلومات عن البوت"""
        embed = discord.Embed(
            title="ℹ️ معلومات البوت | Bot Info",
            description="بوت إدارة النجاة في الصقيع\nWhite Survival Management Bot",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 الإصدار | Version",
            value="1.0.0 - Production Ready",
            inline=True
        )
        
        embed.add_field(
            name="🔧 الحالة | Status",
            value="✅ متصل | Online",
            inline=True
        )
        
        embed.add_field(
            name="🌐 اللغات | Languages",
            value="العربية 🇸🇦 | English 🇬🇧",
            inline=True
        )
        
        embed.add_field(
            name="🎯 الوظائف | Features",
            value=(
                "• نظام التحالفات | Alliance System\n"
                "• نظام الحجوزات | Reservations\n"
                "• نظام التذكيرات | Reminders\n"
                "• نظام الصلاحيات | Permissions\n"
                "• لوحة الإدارة | Admin Panel\n"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👥 الخوادم | Servers",
            value=f"{len(self.bot.guilds)} خادم | servers",
            inline=True
        )
        
        embed.add_field(
            name="👤 المستخدمين | Users",
            value=f"{len(self.bot.users)} مستخدم | users",
            inline=True
        )
        
        embed.set_footer(text="Made with ❤️ for White Survival")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup the cog"""
    await bot.add_cog(HelpSystemCog(bot))
