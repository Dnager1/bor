"""
البوت الرئيسي - Main Bot File
بوت ديسكورد لإدارة مواعيد لعبة النجاة في الصقيع
"""
import discord
from discord.ext import commands
import logging
import sys
import os
from datetime import datetime
import asyncio

from config import config
from database import db

# إعداد نظام السجلات
os.makedirs(config.LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{config.LOGS_DIR}/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# سجل منفصل للأخطاء
error_logger = logging.getLogger('errors')
error_handler = logging.FileHandler(f'{config.LOGS_DIR}/errors.log', encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

# سجل منفصل للحجوزات
bookings_logger = logging.getLogger('bookings')
bookings_handler = logging.FileHandler(f'{config.LOGS_DIR}/bookings.log', encoding='utf-8')
bookings_logger.addHandler(bookings_handler)

logger = logging.getLogger('bot')

class BookingBot(commands.Bot):
    """البوت الرئيسي لإدارة الحجوزات"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=None
        )
        
        self.start_time = datetime.now()
    
    async def setup_hook(self):
        """إعداد البوت"""
        logger.info("🔧 بدء إعداد البوت...")
        
        # تهيئة قاعدة البيانات
        try:
            await db.initialize()
            logger.info("✅ تم تهيئة قاعدة البيانات")
        except Exception as e:
            logger.error(f"❌ فشل تهيئة قاعدة البيانات: {e}")
            raise
        
        # تحميل الـ Cogs
        cogs_to_load = [
            'cogs.bookings',
            'cogs.admin',
            'cogs.admin_panel',
            'cogs.permissions_manager',
            'cogs.stats',
            'cogs.alliance',
            'cogs.alliance_advanced',
            'cogs.help'
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"✅ تم تحميل {cog}")
            except Exception as e:
                logger.error(f"❌ فشل تحميل {cog}: {e}")
        
        # مزامنة الأوامر
        try:
            if config.GUILD_ID:
                guild = discord.Object(id=config.GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"✅ تم مزامنة الأوامر للسيرفر {config.GUILD_ID}")
            else:
                await self.tree.sync()
                logger.info("✅ تم مزامنة الأوامر عالمياً")
        except Exception as e:
            logger.error(f"❌ فشل مزامنة الأوامر: {e}")
        
        logger.info("✅ اكتمل إعداد البوت")
    
    async def on_ready(self):
        """عند جاهزية البوت"""
        logger.info(f"✅ البوت جاهز! تم تسجيل الدخول كـ {self.user}")
        logger.info(f"📊 متصل بـ {len(self.guilds)} سيرفر")
        
        # تعيين حالة البوت
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="مواعيد النجاة في الصقيع | /help"
        )
        await self.change_presence(activity=activity)
        
        # بدء المهام المجدولة
        try:
            await self.load_extension('tasks.reminders_task')
            await self.load_extension('tasks.cleanup_task')
            await self.load_extension('tasks.backup_task')
            logger.info("✅ تم بدء المهام المجدولة")
        except Exception as e:
            logger.error(f"⚠️ تحذير: فشل تحميل المهام المجدولة: {e}")
    
    async def on_guild_join(self, guild):
        """عند انضمام البوت لسيرفر جديد"""
        logger.info(f"✅ انضم البوت إلى سيرفر جديد: {guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild):
        """عند خروج البوت من سيرفر"""
        logger.info(f"❌ خرج البوت من السيرفر: {guild.name} (ID: {guild.id})")
    
    async def on_command_error(self, ctx, error):
        """معالجة أخطاء الأوامر"""
        error_logger.error(f"خطأ في الأمر: {error}", exc_info=error)
    
    async def on_error(self, event, *args, **kwargs):
        """معالجة الأخطاء العامة"""
        error_logger.error(f"خطأ في الحدث {event}", exc_info=sys.exc_info())

async def main():
    """الدالة الرئيسية"""
    # التحقق من الإعدادات
    if not config.validate():
        logger.error("❌ فشل التحقق من الإعدادات")
        return
    
    # إنشاء البوت
    bot = BookingBot()
    
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        await bot.start(config.BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("⏸️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}", exc_info=e)
    finally:
        await bot.close()
        logger.info("👋 تم إغلاق البوت")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏸️ تم إيقاف البوت")
