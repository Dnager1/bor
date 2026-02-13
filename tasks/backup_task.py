"""
مهمة النسخ الاحتياطي - Backup Task
"""
import discord
from discord.ext import commands, tasks
import logging
import shutil
import os
from datetime import datetime

from config import config
from database import db

logger = logging.getLogger('backup')

class BackupTask(commands.Cog):
    """مهمة النسخ الاحتياطي المجدولة"""
    
    def __init__(self, bot):
        self.bot = bot
        self.auto_backup.start()
    
    def cog_unload(self):
        """عند إلغاء تحميل الـ Cog"""
        self.auto_backup.cancel()
    
    @tasks.loop(hours=config.AUTO_BACKUP_HOURS)
    async def auto_backup(self):
        """نسخ احتياطي تلقائي"""
        try:
            logger.info("💾 بدء النسخ الاحتياطي التلقائي...")
            
            # إنشاء مجلد النسخ الاحتياطي
            os.makedirs(config.BACKUP_DIR, exist_ok=True)
            
            # اسم ملف النسخة الاحتياطية
            backup_name = f'auto_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            backup_path = os.path.join(config.BACKUP_DIR, backup_name)
            
            # نسخ قاعدة البيانات
            if os.path.exists(config.DATABASE_PATH):
                shutil.copy2(config.DATABASE_PATH, backup_path)
                
                file_size = os.path.getsize(backup_path) / 1024  # بالكيلوبايت
                
                logger.info(f"✅ تم إنشاء نسخة احتياطية: {backup_name} ({file_size:.2f} KB)")
                
                await db.log_action(
                    'auto_backup',
                    f"تم إنشاء نسخة احتياطية تلقائية: {backup_name}",
                    None,
                    None,
                    f"الحجم: {file_size:.2f} KB"
                )
                
                # حذف النسخ القديمة (الاحتفاظ بآخر 10 نسخ فقط)
                await self.cleanup_old_backups()
            else:
                logger.warning("⚠️ لم يتم العثور على قاعدة البيانات")
            
        except Exception as e:
            logger.error(f"❌ خطأ في النسخ الاحتياطي: {e}", exc_info=e)
    
    async def cleanup_old_backups(self):
        """حذف النسخ الاحتياطية القديمة"""
        try:
            backups = []
            for file in os.listdir(config.BACKUP_DIR):
                if file.startswith('auto_backup_') and file.endswith('.db'):
                    file_path = os.path.join(config.BACKUP_DIR, file)
                    backups.append((file_path, os.path.getmtime(file_path)))
            
            # ترتيب حسب التاريخ
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # حذف ما يزيد عن 10 نسخ
            if len(backups) > 10:
                for backup_path, _ in backups[10:]:
                    os.remove(backup_path)
                    logger.info(f"🗑️ تم حذف نسخة احتياطية قديمة: {os.path.basename(backup_path)}")
        
        except Exception as e:
            logger.error(f"خطأ في تنظيف النسخ الاحتياطية: {e}")
    
    @auto_backup.before_loop
    async def before_backup(self):
        """الانتظار حتى يصبح البوت جاهزاً"""
        await self.bot.wait_until_ready()
        logger.info(f"✅ بدأت مهمة النسخ الاحتياطي (كل {config.AUTO_BACKUP_HOURS} ساعات)")

async def setup(bot):
    """إعداد الـ Cog"""
    await bot.add_cog(BackupTask(bot))
